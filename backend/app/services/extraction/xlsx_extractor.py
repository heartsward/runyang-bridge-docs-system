"""
XLSX/XLS 提取器 —— 关键改进：彻底修 LibreOffice 转 TXT 导致的错位

设计思路：
1. 用 openpyxl 直接读工作簿（不经过 LibreOffice）
2. 重建合并单元格（merge_cells 跟踪）
3. 简单表 → Markdown GFM 表格（| col1 | col2 |）
4. 复杂表（含合并单元格）→ HTML <table> 兜底（Markdown 兼容）
5. 多工作表支持（之前只显示第一个）
6. 同时输出结构化 JSON（用于 AI Wiki / Q&A / 搜索）

Markdown 表格语法限制：不能表达合并单元格。
所以只要检测到合并单元格，就降级到 HTML 表格以保留视觉结构。
"""
import logging
import re
from typing import List, Dict, Any, Tuple, Optional

from .base import BaseExtractor
from .models import ExtractionResult

logger = logging.getLogger(__name__)

# 延迟导入 openpyxl，避免 import-time 错误污染整个模块
try:
    import openpyxl
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


class XlsxExtractor(BaseExtractor):
    SUPPORTED_EXTENSIONS = [".xlsx", ".xls"]

    # 表格大小阈值：超过此行列数视为过大表格
    MAX_ROWS = 1000
    MAX_COLS = 100

    def extract(self, file_path: str) -> ExtractionResult:
        if not OPENPYXL_AVAILABLE:
            return ExtractionResult(error="openpyxl 未安装")

        try:
            self._check_file(file_path)
        except FileNotFoundError as e:
            return ExtractionResult(error=str(e))

        ext = file_path.lower().split(".")[-1]
        try:
            if ext == "xls":
                # 旧版 .xls 需要 xlrd < 2.0 支持；这里尝试，不支持则提示
                return self._extract_xls_legacy(file_path)
            return self._extract_xlsx(file_path)
        except Exception as e:
            logger.exception(f"XlsxExtractor 失败: {file_path}")
            return ExtractionResult(error=f"XLSX 解析失败: {e}")

    def _extract_xlsx(self, file_path: str) -> ExtractionResult:
        """处理 .xlsx 文件"""
        # data_only=True 让公式返回计算后的值而不是公式字符串
        wb = openpyxl.load_workbook(file_path, data_only=True)

        sheets_json: List[Dict[str, Any]] = []
        parts: List[str] = []
        warnings: List[str] = []

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            sheet_md, sheet_json = self._process_sheet(ws, sheet_name)

            if sheet_json.get("truncated"):
                warnings.append(f"工作表 '{sheet_name}' 超过阈值被截断（>{self.MAX_ROWS}行 或 >{self.MAX_COLS}列）")

            sheets_json.append(sheet_json)
            parts.append(f"## 工作表：{sheet_name}\n\n{sheet_md}\n")

        # 文件级别元数据
        file_json = {
            "format": "xlsx",
            "sheet_count": len(wb.sheetnames),
            "sheet_names": list(wb.sheetnames),
        }

        return ExtractionResult(
            markdown="\n".join(parts),
            json_data={"file": file_json, "sheets": sheets_json},
            warnings=warnings,
        )

    def _extract_xls_legacy(self, file_path: str) -> ExtractionResult:
        """处理 .xls 文件：用 LibreOffice 临时转 .xlsx，再用 openpyxl 处理

        旧 .xls 格式（OLE Compound Document）xlrd >= 2.0 已不再支持。
        最稳妥的方式是用 LibreOffice 转 .xlsx 后用 openpyxl 直读。

        注意事项：LibreOffice + subprocess 在 Windows 下对中文文件名支持差，
        所以我们先把源文件拷贝到临时目录并用 ASCII 名，再调用 LibreOffice。
        """
        import subprocess
        import shutil
        import tempfile
        import uuid
        from pathlib import Path

        try:
            # 1. 把源 .xls 拷贝到临时目录，用 ASCII 文件名（避免 LibreOffice 中文名问题）
            workdir = tempfile.mkdtemp(prefix='xls_convert_')
            ascii_xls = Path(workdir) / f"src_{uuid.uuid4().hex[:8]}.xls"
            shutil.copy2(file_path, ascii_xls)

            try:
                # 2. 准备 LibreOffice 输出目录
                outdir = tempfile.mkdtemp(prefix='xls_out_')

                # 3. 找 LibreOffice 可执行文件
                soffice = shutil.which("soffice")
                if not soffice:
                    for win_path in [
                        r"C:\Program Files\LibreOffice\program\soffice.exe",
                        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                    ]:
                        if Path(win_path).exists():
                            soffice = win_path
                            break

                if not soffice:
                    return ExtractionResult(
                        error="未找到 LibreOffice（soffice）。请安装 LibreOffice 或将 .xls 另存为 .xlsx"
                    )

                # 4. 调用 LibreOffice 转换
                cmd = [soffice, "--headless", "--convert-to", "xlsx",
                       "--outdir", outdir, str(ascii_xls)]
                proc = subprocess.run(cmd, capture_output=True, timeout=120)

                # 5. 找转换后的 .xlsx（不依赖原文件名，用通配）
                converted = list(Path(outdir).glob("*.xlsx"))
                if not converted:
                    err_msg = proc.stderr.decode('utf-8', errors='ignore')[:200]
                    return ExtractionResult(
                        error=f".xls 转 .xlsx 失败（输出目录为空）。LibreOffice: {err_msg}"
                    )

                # 6. 用现有 _extract_xlsx 流程处理
                result = self._extract_xlsx(str(converted[0]))
                # 在 JSON 里标记原始格式
                if result.json_data and "file" in result.json_data:
                    result.json_data["file"]["original_format"] = "xls"
                    result.json_data["file"]["converted_via"] = "libreoffice"
                return result
            finally:
                # 清理临时文件
                try:
                    shutil.rmtree(workdir, ignore_errors=True)
                    shutil.rmtree(outdir, ignore_errors=True)
                except Exception:
                    pass

        except FileNotFoundError as e:
            return ExtractionResult(error=f"源文件读取失败: {e}")
        except subprocess.TimeoutExpired:
            return ExtractionResult(error="LibreOffice 转换超时（>120s）")
        except Exception as e:
            logger.exception(f"_extract_xls_legacy 失败: {file_path}")
            return ExtractionResult(error=f".xls 处理失败: {e}")

    def _process_sheet(self, ws, sheet_name: str) -> Tuple[str, Dict[str, Any]]:
        """处理单个工作表 → (markdown, json)"""
        # 找出有效范围（去除尾部全空行/列）
        max_row_raw = ws.max_row or 0
        max_col_raw = ws.max_column or 0

        # 自下而上扫描，裁掉尾部全空行
        max_row = max_row_raw
        while max_row > 0 and self._is_row_empty(ws, max_row, max_col_raw):
            max_row -= 1
        max_col = max_col_raw
        while max_col > 0 and self._is_col_empty(ws, max_col, max_row):
            max_col -= 1

        # 截断标记
        truncated = max_row_raw > self.MAX_ROWS or max_col_raw > self.MAX_COLS
        max_row = min(max_row, self.MAX_ROWS)
        max_col = min(max_col, self.MAX_COLS)

        if max_row == 0 or max_col == 0:
            return "*(空工作表)*", {"name": sheet_name, "empty": True, "truncated": truncated}

        # 收集所有合并单元格区间（用于检测是否需要 HTML 兜底）
        merged_ranges = list(ws.merged_cells.ranges)

        # 提取单元格数据
        rows_data: List[List[Dict[str, Any]]] = []
        for r in range(1, max_row + 1):
            row: List = []
            for c in range(1, max_col + 1):
                cell = ws.cell(row=r, column=c)
                cell_data = {
                    "value": self._format_cell_value(cell.value),
                    "row": r,
                    "col": c,
                }
                # 检查是否在合并区间内（且不是左上角）
                for mr in merged_ranges:
                    if cell.coordinate in mr and cell.coordinate != mr.min_row:
                        # 跳过左上角以外的所有单元格
                        cell_data["merged"] = True
                        break
                row.append(cell_data)
            rows_data.append(row)

        # 选择渲染方式
        if merged_ranges:
            markdown = self._render_html_table(rows_data, merged_ranges, max_row, max_col)
            render_mode = "html"
        else:
            markdown = self._render_markdown_table(rows_data)
            render_mode = "markdown"

        # 结构化 JSON
        sheet_json = {
            "name": sheet_name,
            "render_mode": render_mode,
            "rows": [[c["value"] for c in row] for row in rows_data],
            "merged_ranges": [
                {
                    "min_row": mr.min_row, "min_col": mr.min_col,
                    "max_row": mr.max_row, "max_col": mr.max_col,
                    "value": rows_data[mr.min_row - 1][mr.min_col - 1]["value"] if mr.min_row <= len(rows_data) else "",
                }
                for mr in merged_ranges
            ],
            "truncated": truncated,
        }

        return markdown, sheet_json

    @staticmethod
    def _is_row_empty(ws, row: int, max_col: int) -> bool:
        """检查一行是否全部为空"""
        for c in range(1, max_col + 1):
            if ws.cell(row=row, column=c).value not in (None, ""):
                return False
        return True

    @staticmethod
    def _is_col_empty(ws, col: int, max_row: int) -> bool:
        """检查一列是否全部为空"""
        for r in range(1, max_row + 1):
            if ws.cell(row=r, column=col).value not in (None, ""):
                return False
        return True

    @staticmethod
    def _format_cell_value(value: Any) -> str:
        """格式化单元格值为字符串"""
        if value is None:
            return ""
        if isinstance(value, float):
            # 整数浮点数显示为整数
            if value == int(value):
                return str(int(value))
            return str(value)
        if isinstance(value, bool):
            return "✓" if value else "✗"
        # datetime / date
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        s = str(value).strip()
        # 清理 Markdown 表格特殊字符
        s = s.replace("|", "\\|").replace("\n", " ").replace("\r", " ")
        return s

    @staticmethod
    def _render_markdown_table(rows_data: List[List[Dict[str, Any]]]) -> str:
        """渲染简单 Markdown 表格（无合并单元格）"""
        if not rows_data:
            return ""
        col_count = max(len(r) for r in rows_data)

        lines: List[str] = []
        # 表头（第一行）
        header = "| " + " | ".join(c["value"] for c in rows_data[0]) + " |"
        # 补齐列数
        if len(rows_data[0]) < col_count:
            header = header.rstrip(" |") + " |" + " |".join([""] * (col_count - len(rows_data[0]))) + " |"
        lines.append(header)

        # 分隔行
        lines.append("| " + " | ".join(["---"] * col_count) + " |")

        # 数据行
        for row in rows_data[1:]:
            cells = [c["value"] for c in row]
            if len(cells) < col_count:
                cells.extend([""] * (col_count - len(cells)))
            lines.append("| " + " | ".join(cells) + " |")

        return "\n".join(lines)

    @staticmethod
    def _render_html_table(rows_data, merged_ranges, max_row: int, max_col: int) -> str:
        """渲染 HTML 表格（保留合并单元格结构）"""
        # 构建合并查找表：(r,c) → 主格 (mr.min_row, mr.min_col)
        # 未合并的格子不在 merge_owner 中
        merge_owner: Dict[Tuple[int, int], Tuple[int, int]] = {}
        for mr in merged_ranges:
            for r in range(mr.min_row, mr.max_row + 1):
                for c in range(mr.min_col, mr.max_col + 1):
                    merge_owner[(r, c)] = (mr.min_row, mr.min_col)

        # 构建主格查找（行/列 → 主格 mr 对象），用于查 rowspan/colspan
        merged_cells_set = set()
        for mr in merged_ranges:
            merged_cells_set.add((mr.min_row, mr.min_col))

        cells_html: List[str] = []
        for r_idx, row in enumerate(rows_data, start=1):
            cells_in_row: List[str] = []
            for c_idx, cell in enumerate(row, start=1):
                # 跳过被合并的从格（merge_owner 中记录了从格 → 主格；主格 → 主格）
                # 未合并格子：merge_owner.get((r,c), (r,c)) == (r,c) → 不跳过
                owner = merge_owner.get((r_idx, c_idx), (r_idx, c_idx))
                if owner != (r_idx, c_idx):
                    # 这是被合并的从格
                    continue

                # 计算合并跨度（只在主格上有 rowspan/colspan）
                rowspan, colspan = 1, 1
                if (r_idx, c_idx) in merged_cells_set:
                    for mr in merged_ranges:
                        if (r_idx, c_idx) == (mr.min_row, mr.min_col):
                            rowspan = mr.max_row - mr.min_row + 1
                            colspan = mr.max_col - mr.min_col + 1
                            break

                value = cell["value"]
                # HTML 转义
                value = (value.replace("&", "&amp;")
                              .replace("<", "&lt;")
                              .replace(">", "&gt;"))
                rowspan_attr = f' rowspan="{rowspan}"' if rowspan > 1 else ''
                colspan_attr = f' colspan="{colspan}"' if colspan > 1 else ''
                cells_in_row.append(f"<td{rowspan_attr}{colspan_attr}>{value}</td>")
            cells_html.append("<tr>" + "".join(cells_in_row) + "</tr>")

        # 用内联样式让表格紧凑、可对齐
        return (
            "<table border=\"1\" cellspacing=\"0\" cellpadding=\"4\" "
            "style=\"border-collapse:collapse;font-size:13px;\">"
            + "\n".join(cells_html)
            + "</table>"
        )