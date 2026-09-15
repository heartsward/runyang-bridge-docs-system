# -*- coding: utf-8 -*-
"""
Office 格式 → PDF 预览转换器（阶段二十四）

设计要点：
- 仅用于"原文件"模式的 PDF 预览，不参与内容提取（提取链路继续走 anydoc）
- 缓存：backend/cache/converted_pdfs/{doc_id}.pdf；按 doc_id + 原文件 mtime 比对失效
- 进度状态：task_status/preview_convert_{doc_id}.json（独立通道，与内容提取
  的 extract_{doc_id}_*.json 完全不互相干扰）
- 跨进程文件锁：避免 LibreOffice 同实例冲突（LibreOffice 不允许多实例）

支持格式（LibreOffice 7.6 实测可转 PDF，阶段二十六·26.3 共 20 种）：
- .doc / .docx / .docm
- .xls / .xlsx / .xlsm / .xlsb
- .ppt / .pptx / .pptm / .pps / .ppsx / .ppsm / .pot
- .odt / .ods / .odp
- .rtf / .epub
- .csv（文本类，但 LibreOffice 转得更整齐）

不支持：.pdf（已是 PDF）/ 图片（直接显示）/ .txt / .md 等纯文本（无"原文件"切换，走提取内容）
"""
import json
import logging
import os
import platform
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 阶段二十六·26.3：LibreOffice 支持转 PDF 的格式（20 种）
# - Word 3 种：.doc/.docx/.docm
# - Excel 4 种：.xls/.xlsx/.xlsm/.xlsb
# - PowerPoint 7 种：.ppt/.pptx/.pptm/.pps/.ppsx/.ppsm/.pot
# - .csv / .epub
# - OpenDocument / RTF：.odt/.ods/.odp/.rtf
SUPPORTED_OFFICE_TYPES = frozenset({
    # Word 3 种
    ".doc", ".docx", ".docm",
    # Excel 4 种
    ".xls", ".xlsx", ".xlsm", ".xlsb",
    # PowerPoint 7 种
    ".ppt", ".pptx", ".pptm",
    ".pps", ".ppsx", ".ppsm",
    ".pot",
    # CSV / EPUB
    ".csv",
    ".epub",
    # OpenDocument / RTF
    ".odt", ".ods", ".odp",
    ".rtf",
})

# 已 PDF/图片等不需要 LibreOffice 转换（前端走 iframe / 图片直显 / 已 PDF 不需转）
UNSUPPORTED_FOR_CONVERT = frozenset({
    ".pdf",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg",
})

# 缓存目录（首次创建）
CACHE_DIR = Path(__file__).resolve().parents[2] / "cache" / "converted_pdfs"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 任务状态目录（沿用现有 task_status）
TASK_STATUS_DIR = Path(__file__).resolve().parents[2] / "task_status"
TASK_STATUS_DIR.mkdir(parents=True, exist_ok=True)

# 跨进程文件锁目录
LOCK_DIR = Path(__file__).resolve().parents[2] / "cache" / "soffice_locks"
LOCK_DIR.mkdir(parents=True, exist_ok=True)


def is_supported_office_type(file_type: str) -> bool:
    """判断扩展名是否走 LibreOffice 转换"""
    if not file_type:
        return False
    ext = "." + file_type.lower().lstrip(".")
    return ext in SUPPORTED_OFFICE_TYPES


def detect_soffice_path() -> Optional[str]:
    """探测系统 soffice 可执行文件路径

    探测顺序（先 .env 自定义，再平台标准路径，最后 PATH 兜底）
    """
    from app.core.config import settings

    # 1. 用户在 .env 显式配置的路径（优先级最高）
    custom = (settings.LIBREOFFICE_BIN_PATH or "").strip()
    if custom and os.path.isfile(custom):
        return custom

    system = platform.system().lower()

    # 2. 平台标准路径
    candidates = []
    if system == "windows":
        candidates = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
    elif system == "darwin":  # macOS
        candidates = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]
    else:  # linux / bsd
        candidates = [
            "/usr/bin/soffice",
            "/usr/bin/libreoffice",
            "/opt/libreoffice/program/soffice",
            "/snap/bin/libreoffice",
        ]

    for p in candidates:
        if os.path.isfile(p):
            return p

    # 3. PATH 兜底（Windows 装时勾选了"加到 PATH"才有效）
    which = shutil.which("soffice") or shutil.which("libreoffice")
    if which:
        return which

    return None


def get_version_string(soffice_path: str) -> str:
    """调 soffice --version 拿版本号（带超时）

    阶段二十六·26.5+26.8：Windows 下彻底静默（--headless + CREATE_NO_WINDOW +
    CREATE_DETACHED_PROCESS + STARTUPINFO wShowWindow=SW_HIDE 四重保险），
    防止 LibreOffice 首次 profile 初始化时弹 "Welcome to LibreOffice" 窗口。
    """
    creationflags = 0
    startupinfo = None
    if platform.system() == "Windows":
        creationflags = subprocess.CREATE_NO_WINDOW | 0x00000008  # CREATE_DETACHED_PROCESS
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
    try:
        out = subprocess.run(
            [soffice_path, "--headless", "--version"],
            capture_output=True, text=True, timeout=10,
            creationflags=creationflags,
            startupinfo=startupinfo,
        )
        return (out.stdout or out.stderr or "").strip().split("\n")[0]
    except Exception as e:
        return f"unknown ({e})"


class _PreviewStatusStore:
    """进度状态读写 — 独立通道（与 extract_{id}_*.json 完全分离）

    单文件覆盖式：每次更新直接覆盖同一文件。
    并发安全：写时用临时文件 + rename 原子写。
    """
    @staticmethod
    def _path(doc_id: int) -> Path:
        return TASK_STATUS_DIR / f"preview_convert_{doc_id}.json"

    @staticmethod
    def read(doc_id: int) -> Dict[str, Any]:
        p = _PreviewStatusStore._path(doc_id)
        if not p.exists():
            return {
                "doc_id": doc_id,
                "status": "idle",
                "started_at": None,
                "finished_at": None,
                "elapsed_sec": 0,
                "output_size": None,
                "error_msg": None,
            }
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[PreviewConverter] 读状态失败 doc_id={doc_id}: {e}")
            return {"doc_id": doc_id, "status": "idle", "error_msg": str(e)}

    @staticmethod
    def write(doc_id: int, payload: Dict[str, Any]) -> None:
        p = _PreviewStatusStore._path(doc_id)
        tmp = p.with_suffix(f".json.tmp.{uuid.uuid4().hex[:8]}")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, p)
        except Exception as e:
            logger.warning(f"[PreviewConverter] 写状态失败 doc_id={doc_id}: {e}")
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass

    @staticmethod
    def clear(doc_id: int) -> None:
        p = _PreviewStatusStore._path(doc_id)
        p.unlink(missing_ok=True)


class PreviewConverter:
    """Office → PDF 预览转换器（单例）

    用法：
        converter = PreviewConverter()
        # 探测 soffice（应用启动时调一次）
        converter.bootstrap()
        # 触发转换（异步；非阻塞）
        await converter.trigger_async(doc_id, file_path, file_type)
        # 同步取缓存或触发转换（小文件秒出）
        pdf_path = await converter.get_or_convert(doc_id, file_path, file_type)
    """

    def __init__(self):
        self._soffice_path: Optional[str] = None
        self._soffice_version: str = ""
        self._available: bool = False
        # 进程内并发锁（防同线程池并发）
        self._thread_lock = threading.Lock()
        # 跨进程文件锁（key=doc_id；防多 worker 进程同时转同 doc）
        self._file_locks: Dict[int, "_FileLock"] = {}

    # ---------- 启动探测 ----------
    def bootstrap(self) -> bool:
        """探测 LibreOffice 并缓存路径/版本。返回是否可用。"""
        path = detect_soffice_path()
        if not path:
            logger.warning(
                "[PreviewConverter] ⚠️ LibreOffice 未安装或不在 PATH。"
                "Office 格式在线预览不可用,用户需下载查看。"
                "参见 docs/环境安装-LibreOffice.md"
            )
            self._available = False
            return False
        self._soffice_path = path
        self._soffice_version = get_version_string(path)
        logger.info(f"[PreviewConverter] LibreOffice 已找到: {path} ({self._soffice_version})")
        self._available = True
        return True

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def soffice_path(self) -> Optional[str]:
        return self._soffice_path

    # ---------- 缓存管理 ----------
    def _cache_path(self, doc_id: int) -> Path:
        return CACHE_DIR / f"{doc_id}.pdf"

    def get_cached_pdf(self, doc_id: int) -> Optional[Path]:
        """拿缓存的 PDF（None 表示无缓存或已失效）"""
        p = self._cache_path(doc_id)
        if p.exists() and p.stat().st_size > 0:
            return p
        return None

    def invalidate_cache(self, doc_id: int) -> None:
        """清掉某 doc 的缓存（文档被覆盖上传后调用）"""
        p = self._cache_path(doc_id)
        p.unlink(missing_ok=True)
        # 同步清指纹，否则下次 _is_cache_fresh 还会看到旧指纹
        self._fingerprint_path(doc_id).unlink(missing_ok=True)
        _PreviewStatusStore.clear(doc_id)

    def _is_cache_fresh(self, doc_id: int, source_path: str) -> bool:
        """缓存是否新鲜（存在 + 源文件大小/指纹匹配）

        阶段二十六·26.8 重要修复：之前只比 mtime，但 Windows 覆盖上传时默认会**保留旧文件的 mtime**，
        导致新文件覆盖旧文件后 mtime 不变 → 缓存被判定为"新鲜" → 返回旧 PDF → 预览空白。
        现改为同时比对**源文件大小 + 头 4096 字节**（快速指纹，覆盖写也保证不同）。
        """
        cached = self.get_cached_pdf(doc_id)
        if not cached:
            return False
        if not os.path.exists(source_path):
            return False
        try:
            src_stat = os.stat(source_path)
            # 1) 大小匹配（最便宜的判定：覆盖写新文件大小通常不同）
            fingerprint_path = self._fingerprint_path(doc_id)
            if fingerprint_path.exists():
                try:
                    saved = json.loads(fingerprint_path.read_text(encoding="utf-8"))
                    saved_size = saved.get("source_size", -1)
                    saved_head = saved.get("source_head", "")
                    # 大小不同 → 源文件变了 → 缓存失效
                    if saved_size != src_stat.st_size:
                        logger.info(f"[PreviewConverter] doc {doc_id} 源文件大小变化 {saved_size}→{src_stat.st_size}，缓存失效")
                        return False
                    # 读源文件前 4096 字节比指纹
                    with open(source_path, "rb") as f:
                        head = f.read(4096)
                    if saved_head != head.decode("utf-8", errors="replace"):
                        logger.info(f"[PreviewConverter] doc {doc_id} 源文件内容变化（头哈希不同），缓存失效")
                        return False
                except Exception:
                    # 指纹文件坏了，保守按陈旧处理 → 重转
                    return False
            # 2) 没有指纹文件（旧版本遗留）→ 仅按 mtime 兜底
            return cached.stat().st_mtime >= src_stat.st_mtime
        except Exception:
            return False

    def _fingerprint_path(self, doc_id: int) -> Path:
        """源文件指纹（大小 + 头 4096 字节），用于缓存失效判定。"""
        return CACHE_DIR / f"{doc_id}.source.fp.json"

    def _save_fingerprint(self, doc_id: int, source_path: str) -> None:
        """转换成功后保存源文件指纹，便于下次精确判定。"""
        try:
            src_stat = os.stat(source_path)
            with open(source_path, "rb") as f:
                head = f.read(4096)
            payload = {
                "source_size": src_stat.st_size,
                "source_head": head.decode("utf-8", errors="replace"),
                "saved_at": time.time(),
            }
            self._fingerprint_path(doc_id).write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"[PreviewConverter] 保存指纹失败 doc={doc_id}: {e}")

    # ---------- 文件锁 ----------
    def _get_file_lock(self, doc_id: int) -> "_FileLock":
        if doc_id not in self._file_locks:
            self._file_locks[doc_id] = _FileLock(LOCK_DIR / f"doc_{doc_id}.lock")
        return self._file_locks[doc_id]

    # ---------- 同步转换（阻塞）----------
    def convert_blocking(self, doc_id: int, file_path: str, file_type: str) -> Path:
        """同步阻塞转换。调用方负责包装到 executor / thread。

        Raises:
            RuntimeError: LibreOffice 不可用 / 转换失败 / 超时
        """
        if not self._available:
            raise RuntimeError(
                "LibreOffice 未安装,无法转换。"
                "参见 docs/环境安装-LibreOffice.md 安装 LibreOffice 7.0+"
            )
        if not is_supported_office_type(file_type):
            raise RuntimeError(f"不支持的文件类型: {file_type}")

        # 缓存命中直接返回
        if self._is_cache_fresh(doc_id, file_path):
            cached = self.get_cached_pdf(doc_id)
            assert cached is not None
            logger.info(f"[PreviewConverter] doc {doc_id} 命中缓存 ({cached.stat().st_size} B)")
            return cached

        from app.core.config import settings
        timeout = settings.PREVIEW_CONVERT_TIMEOUT

        _PreviewStatusStore.write(doc_id, {
            "doc_id": doc_id,
            "status": "converting",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "finished_at": None,
            "elapsed_sec": 0,
            "output_size": None,
            "error_msg": None,
        })

        # 进程内 + 跨进程文件锁
        file_lock = self._get_file_lock(doc_id)
        t0 = time.monotonic()
        with self._thread_lock, file_lock:
            # 二次检查：进锁后可能别的进程刚转好
            if self._is_cache_fresh(doc_id, file_path):
                cached = self.get_cached_pdf(doc_id)
                assert cached is not None
                _PreviewStatusStore.write(doc_id, {
                    "doc_id": doc_id, "status": "ready",
                    "started_at": None, "finished_at": datetime.utcnow().isoformat() + "Z",
                    "elapsed_sec": round(time.monotonic() - t0, 1),
                    "output_size": cached.stat().st_size, "error_msg": None,
                })
                return cached

            try:
                pdf_bytes = self._call_soffice(file_path, timeout)
                # 把 PDF 字节写入缓存
                target = self._cache_path(doc_id)
                target.write_bytes(pdf_bytes)
                # 保存源文件指纹（大小+头），下次可精确判定缓存是否有效
                self._save_fingerprint(doc_id, file_path)
                elapsed = round(time.monotonic() - t0, 1)
                _PreviewStatusStore.write(doc_id, {
                    "doc_id": doc_id, "status": "ready",
                    "started_at": None, "finished_at": datetime.utcnow().isoformat() + "Z",
                    "elapsed_sec": elapsed,
                    "output_size": target.stat().st_size, "error_msg": None,
                })
                logger.info(f"[PreviewConverter] doc {doc_id} 转换成功 ({elapsed}s, {target.stat().st_size} B)")
                return target
            except Exception as e:
                elapsed = round(time.monotonic() - t0, 1)
                err_msg = f"{type(e).__name__}: {e}"
                _PreviewStatusStore.write(doc_id, {
                    "doc_id": doc_id, "status": "error",
                    "started_at": None, "finished_at": datetime.utcnow().isoformat() + "Z",
                    "elapsed_sec": elapsed,
                    "output_size": None, "error_msg": err_msg,
                })
                logger.exception(f"[PreviewConverter] doc {doc_id} 转换失败 ({elapsed}s)")
                raise RuntimeError(err_msg) from e

    def _call_soffice(self, file_path: str, timeout: int) -> bytes:
        """调 soffice --convert-to pdf,返回生成的 PDF 字节内容

        注：返回 bytes 而非路径，是因为 TemporaryDirectory 的 __exit__ 会在 with 块
        退出时清理目录；若返回路径，外层调用时文件已不存在（踩坑记录）。
        """
        assert self._soffice_path, "LibreOffice 路径未初始化（请先调 bootstrap()）"

        # 临时输出目录（LibreOffice 会把同名 .pdf 写到这里）
        with tempfile.TemporaryDirectory(prefix="lo_convert_") as tmpdir:
            # 临时 user profile 防污染用户配置 + 防同时多实例冲突
            profile_dir = Path(tmpdir) / "lo_profile"
            profile_uri = profile_dir.as_uri()  # file:///...

            cmd = [
                self._soffice_path,
                "--headless",
                "--norestore",  # 不恢复上次会话
                "--nolockcheck",  # 不检查别的实例（我们自己加锁）
                "--nologo",
                "--nodefault",
                "--nofirststartwizard",
                "--convert-to", "pdf",
                "--outdir", tmpdir,
                f"-env:UserInstallation={profile_uri}",
                file_path,
            ]
            logger.debug(f"[PreviewConverter] soffice cmd: {' '.join(cmd)}")

            # Windows:不弹出 cmd 控制台窗口（静默运行 LibreOffice 子进程）
            # CREATE_NO_WINDOW = 0x08000000；仅 Windows 有效，其它平台忽略
            # 阶段二十六·26.8 加：CREATE_DETACHED_PROCESS（0x00000008）+ STARTUPINFO wShowWindow=SW_HIDE
            # 双保险防止 LibreOffice 首次 profile 初始化时弹 "Welcome to LibreOffice" 窗口
            creationflags = 0
            startupinfo = None
            if platform.system() == "Windows":
                creationflags = subprocess.CREATE_NO_WINDOW | 0x00000008  # CREATE_DETACHED_PROCESS
                # SW_HIDE = 0，彻底隐藏窗口
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=creationflags,
                    startupinfo=startupinfo,
                )
            except subprocess.TimeoutExpired as e:
                raise RuntimeError(f"soffice 转换超时 ({timeout}s)") from e

            if result.returncode != 0:
                err = (result.stderr or result.stdout or "").strip()
                raise RuntimeError(f"soffice 返回非零退出码 {result.returncode}: {err[:500]}")

            # soffice 会生成与输入同名的 .pdf（连扩展名都换）
            src_stem = Path(file_path).stem
            pdf_out = Path(tmpdir) / f"{src_stem}.pdf"
            if not pdf_out.exists() or pdf_out.stat().st_size == 0:
                raise RuntimeError(f"soffice 未生成 PDF 输出（期望 {pdf_out}）")

            # 立即读字节（__exit__ 会清理 tmpdir）
            return pdf_out.read_bytes()

    # ---------- 异步 / 状态查询 ----------
    async def get_or_convert(
        self,
        doc_id: int,
        file_path: str,
        file_type: str,
    ) -> Path:
        """缓存命中直接返回；否则同步转（小文件秒出）。

        适合 FastAPI 端点直接 await。
        """
        # 缓存命中
        if self._is_cache_fresh(doc_id, file_path):
            cached = self.get_cached_pdf(doc_id)
            if cached:
                return cached
        # 否则同步触发转换
        return self.convert_blocking(doc_id, file_path, file_type)

    async def trigger_async(
        self,
        doc_id: int,
        file_path: str,
        file_type: str,
    ) -> None:
        """异步触发转换（不阻塞当前请求）

        适合"用户进预览页前预热"或"上传后立即预热下次秒出"。
        """
        import asyncio
        loop = asyncio.get_event_loop()
        # 缓存命中则跳过
        if self._is_cache_fresh(doc_id, file_path):
            return
        # 已在 converting 状态则跳过(避免重复触发)
        cur = _PreviewStatusStore.read(doc_id)
        if cur.get("status") == "converting":
            return
        # 推到线程池跑
        await loop.run_in_executor(
            None,
            lambda: self.convert_blocking(doc_id, file_path, file_type),
        )

    def get_status(self, doc_id: int) -> Dict[str, Any]:
        """前端轮询用：返回当前转换状态

        状态机:idle → converting → ready | error
        """
        # 缓存命中时直接报 ready（不查状态文件，覆盖式写入可能晚到）
        cached = self.get_cached_pdf(doc_id)
        if cached and cached.stat().st_size > 0:
            return {
                "doc_id": doc_id,
                "status": "ready",
                "started_at": None,
                "finished_at": None,
                "elapsed_sec": 0,
                "output_size": cached.stat().st_size,
                "error_msg": None,
                "from_cache": True,
            }
        return _PreviewStatusStore.read(doc_id)


class _FileLock:
    """跨进程文件锁 — 简单实现：基于 fcntl.flock（Linux/macOS）或 msvcrt.locking（Windows）

    Fallback 顺序：
    1. fcntl.flock(LOCK_EX) — Linux/macOS
    2. msvcrt.locking(LK_NBLCK) — Windows
    3. 仅进程内锁 — 都不支持时
    """

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self._lock_type = self._detect_type()

    @staticmethod
    def _detect_type() -> str:
        if platform.system() != "Windows":
            try:
                import fcntl  # noqa: F401
                return "fcntl"
            except ImportError:
                pass
        try:
            import msvcrt  # noqa: F401
            return "msvcrt"
        except ImportError:
            return "noop"

    def __enter__(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = open(self.lock_path, "w")
        if self._lock_type == "fcntl":
            import fcntl
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX)
        elif self._lock_type == "msvcrt":
            import msvcrt
            # 锁 1 字节；LOCK_EX 等价
            while True:
                try:
                    msvcrt.locking(self._fd.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.1)
        # noop: 不跨进程同步（仅依赖进程内锁 + soffice single-instance 自然排队）
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self._lock_type == "fcntl":
                import fcntl
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            elif self._lock_type == "msvcrt":
                import msvcrt
                msvcrt.locking(self._fd.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            try:
                self._fd.close()
            except Exception:
                pass


# 模块级单例
_converter_instance: Optional[PreviewConverter] = None


def get_preview_converter() -> PreviewConverter:
    """获取单例（应用启动时调 bootstrap() 探测 LibreOffice）"""
    global _converter_instance
    if _converter_instance is None:
        _converter_instance = PreviewConverter()
        _converter_instance.bootstrap()
    return _converter_instance