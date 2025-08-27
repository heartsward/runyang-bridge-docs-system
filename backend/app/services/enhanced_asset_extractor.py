# -*- coding: utf-8 -*-
"""
增强版设备资产信息提取器
支持智能编码检测和更全面的字段映射
"""
import re
import csv
import json
import pandas as pd
from io import StringIO, BytesIO
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import ipaddress
from pathlib import Path
import logging

# 尝试导入，如果失败则使用字符串常量
try:
    from app.models.asset import AssetType, AssetStatus, NetworkLocation
    from app.schemas.asset import AssetCreate
    from app.utils.encoding_detector import EncodingDetector
except ImportError:
    # 如果导入失败，定义常量
    class AssetType:
        SERVER = "server"
        NETWORK = "network"
        STORAGE = "storage"
        SECURITY = "security"
        DATABASE = "database"
        APPLICATION = "application"
        OTHER = "other"
    
    class AssetStatus:
        ACTIVE = "active"
        INACTIVE = "inactive"
        MAINTENANCE = "maintenance"
        RETIRED = "retired"
    
    class NetworkLocation:
        OFFICE = "office"
        MONITORING = "monitoring"
        BILLING = "billing"
    
    # 简化版编码检测器
    class EncodingDetector:
        @staticmethod
        def detect_encoding(file_path, sample_size=8192):
            import chardet
            try:
                with open(file_path, 'rb') as f:
                    raw_data = f.read(sample_size)
                result = chardet.detect(raw_data)
                return result.get('encoding', 'utf-8'), result.get('confidence', 0.5)
            except:
                return 'utf-8', 0.5

logger = logging.getLogger(__name__)

class EnhancedAssetExtractor:
    """增强版设备资产信息提取器"""
    
    def __init__(self):
        self.encoding_detector = EncodingDetector()
        self.ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        self.mac_pattern = re.compile(r'\b[0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}\b')
        self.hostname_pattern = re.compile(r'[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*')
        
        # 扩展的中文字段映射关系
        self.field_mappings = {
            'name': ['name', 'device_name', 'hostname', 'host', '设备名', '设备名称', '主机名', '名称', '资产名称'],
            'ip': ['ip', 'ip_address', 'ip地址', 'IP地址', 'IP', 'host', '主机IP', '管理IP', '设备地址', '设备IP', '地址', '访问地址', '连接地址'],
            'hostname': ['hostname', 'host', '主机名', '设备名', 'device_name', 'name', 'server_name'],
            'username': ['username', 'user', '用户名', '用户', 'login', 'account', '登录用户', '管理用户'],
            'password': ['password', 'pwd', '密码', 'pass', 'passwd', '登录密码', '管理密码'],
            'port': ['port', '端口', 'ssh_port', 'port_num', '管理端口', 'telnet_port'],
            'os': ['os', 'system', '操作系统', 'os_version', '系统版本', '系统', 'operating_system'],
            'type': ['type', 'device_type', '设备类型', '类型', 'category', '分类', '资产类型'],
            'model': ['model', '型号', 'device_model', '设备型号', '产品型号', 'product_model'],
            'manufacturer': ['manufacturer', '厂商', '制造商', 'vendor', 'brand', '品牌', '生产厂商'],
            'serial': ['serial', 'serial_number', 'sn', '序列号', '产品序列号', 'product_sn'],
            'location': ['location', '位置', '机房', 'datacenter', '数据中心', '所在位置', '安装位置'],
            'department': ['department', '部门', 'dept', 'team', '所属部门', '管理部门', '科室'],
            'status': ['status', '状态', '运行状态', '设备状态', '工作状态', 'state'],
            'notes': ['notes', 'note', '备注', '说明', 'description', 'remark', '描述', '备注信息'],
            'rack': ['rack', 'rack_position', 'u_position', '机架', '机架位置', 'U位', '机位'],
            'cpu': ['cpu', 'processor', '处理器', 'cpu_info', 'cpu型号', '中央处理器'],
            'memory': ['memory', 'ram', '内存', 'mem', '内存大小', '内存容量'],
            'storage': ['storage', 'disk', '存储', '磁盘', 'hdd', 'ssd', '硬盘', '存储容量'],
            'mac': ['mac', 'mac_address', 'mac地址', 'MAC地址', 'MAC', '物理地址'],
            'service': ['service', '服务', 'application', '应用', '业务', '服务名'],
            'purpose': ['purpose', '用途', '业务用途', '使用用途', 'usage'],
            'purchase_date': ['purchase_date', '采购日期', '购买日期', 'buy_date'],
            'warranty': ['warranty', 'warranty_expiry', '保修期', '质保期', '保修到期'],
            'network_location': ['network_location', '网络位置', '网络区域', '网络环境']
        }
    
    def extract_from_file(self, file_path: str, file_content: bytes, file_type: str) -> List[Dict[str, Any]]:
        """从文件中提取资产信息"""
        logger.info(f"开始提取资产信息: 文件={file_path}, 类型={file_type}, 大小={len(file_content)}字节")
        
        try:
            if file_type.lower() in ['csv']:
                return self._extract_from_csv(file_content, file_path)
            elif file_type.lower() in ['xlsx', 'xls']:
                return self._extract_from_excel(file_content, file_path)
            elif file_type.lower() in ['txt', 'md']:
                return self._extract_from_text_file(file_content, file_path)
            elif file_type.lower() in ['json']:
                return self._extract_from_json_file(file_content, file_path)
            else:
                # 尝试从文本中提取
                return self._extract_from_text_file(file_content, file_path)
        except Exception as e:
            logger.error(f"提取文件内容时发生错误: {str(e)}")
            return []
    
    def extract_from_text(self, text_content: str) -> List[Dict[str, Any]]:
        """从文本内容中提取资产信息（公共接口）"""
        try:
            logger.info(f"开始从文本提取资产信息，文本长度: {len(text_content)} 字符")
            
            # 首先尝试检测是否为JSON格式
            text_stripped = text_content.strip()
            if (text_stripped.startswith('{') and text_stripped.endswith('}')) or \
               (text_stripped.startswith('[') and text_stripped.endswith(']')):
                logger.info("检测到JSON格式，使用JSON解析器")
                try:
                    import json
                    json.loads(text_content)  # 验证是否为有效JSON
                    return self._extract_from_json_text(text_content)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON格式验证失败: {e}，回退到文本解析")
            
            # 否则使用文本解析
            logger.info("使用文本解析器")
            return self._extract_from_text(text_content)
        except Exception as e:
            logger.error(f"文本提取失败: {str(e)}")
            return []
    
    def _extract_from_json_text(self, text_content: str) -> List[Dict[str, Any]]:
        """从JSON文本中提取资产信息"""
        try:
            data = json.loads(text_content)
            assets = []
            
            if isinstance(data, list):
                # 直接是资产数组
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        asset_data = self._map_fields(item, f"JSON第{i+1}项")
                        if asset_data and (asset_data.get('ip_address') or asset_data.get('hostname') or asset_data.get('name')):
                            assets.append(asset_data)
            elif isinstance(data, dict):
                # 检查是否包含assets数组字段
                if 'assets' in data and isinstance(data['assets'], list):
                    logger.info(f"检测到包含assets数组的JSON结构，共{len(data['assets'])}个资产")
                    for i, item in enumerate(data['assets']):
                        if isinstance(item, dict):
                            logger.info(f"处理Assets数组第{i+1}项: {list(item.keys())}")
                            asset_data = self._map_fields(item, f"Assets数组第{i+1}项")
                            if asset_data:
                                logger.info(f"映射结果: {asset_data}")
                                # 更严格的验证：必须有name或ip_address
                                if asset_data.get('name') or asset_data.get('ip_address'):
                                    assets.append(asset_data)
                                    logger.info(f"添加资产: {asset_data.get('name', asset_data.get('ip_address'))}")
                                else:
                                    logger.warning(f"跳过无效资产 (缺少name和ip_address): {asset_data}")
                            else:
                                logger.warning(f"映射失败的项: {item}")
                else:
                    # 检查其他可能的数组字段名
                    array_fields = ['items', 'data', 'devices', 'nodes', 'hosts', 'servers']
                    found_array = False
                    
                    for field in array_fields:
                        if field in data and isinstance(data[field], list):
                            logger.info(f"检测到包含{field}数组的JSON结构，共{len(data[field])}个资产")
                            for i, item in enumerate(data[field]):
                                if isinstance(item, dict):
                                    asset_data = self._map_fields(item, f"{field}数组第{i+1}项")
                                    if asset_data and (asset_data.get('name') or asset_data.get('ip_address')):
                                        assets.append(asset_data)
                            found_array = True
                            break
                    
                    if not found_array:
                        # 将根对象当作单个资产处理
                        asset_data = self._map_fields(data, "JSON根对象")
                        if asset_data and (asset_data.get('name') or asset_data.get('ip_address')):
                            assets.append(asset_data)
            
            logger.info(f"JSON解析完成，总共提取 {len(assets)} 个资产")
            return assets
            
        except Exception as e:
            logger.error(f"JSON文本解析错误: {str(e)}")
            return []
    
    def _extract_from_excel(self, content: bytes, file_path: str) -> List[Dict[str, Any]]:
        """从Excel文件提取资产信息（转换为CSV后处理）"""
        logger.info(f"开始解析Excel文件: {file_path}")
        logger.info("使用Excel转CSV策略，避免复杂的数据类型处理")
        
        try:
            excel_file = BytesIO(content)
            
            # 根据文件扩展名选择合适的引擎
            file_ext = file_path.lower().split('.')[-1] if '.' in file_path else 'xlsx'
            engine = 'xlrd' if file_ext == 'xls' else 'openpyxl'
            logger.info(f"文件类型: {file_ext}, 使用引擎: {engine}")
            
            # 尝试读取所有工作表
            try:
                excel_data = pd.ExcelFile(excel_file, engine=engine)
            except Exception as e:
                logger.warning(f"使用引擎{engine}失败: {e}")
                # 尝试其他引擎
                alt_engine = 'openpyxl' if engine == 'xlrd' else 'xlrd'
                try:
                    excel_data = pd.ExcelFile(excel_file, engine=alt_engine)
                    engine = alt_engine
                    logger.info(f"切换到引擎{engine}成功")
                except Exception as e2:
                    logger.error(f"所有引擎都失败: {e2}")
                    return []
            
            logger.info(f"Excel工作表列表: {excel_data.sheet_names}")
            
            # 合并所有工作表数据
            all_dataframes = []
            
            for sheet_name in excel_data.sheet_names:
                logger.info(f"读取工作表: {sheet_name}")
                
                try:
                    # 尝试不同的读取参数
                    df = None
                    
                    for skip_rows in [0, 1, 2]:
                        try:
                            if skip_rows == 0:
                                df = pd.read_excel(excel_file, sheet_name=sheet_name, engine=engine)
                            else:
                                df = pd.read_excel(excel_file, sheet_name=sheet_name, engine=engine, skiprows=skip_rows)
                            
                            logger.info(f"成功读取工作表 {sheet_name} (跳过{skip_rows}行): {df.shape[0]}行 x {df.shape[1]}列")
                            break
                        except Exception as e:
                            if skip_rows == 2:
                                logger.error(f"读取工作表 {sheet_name} 失败: {e}")
                                continue
                    
                    if df is not None and not df.empty:
                        # 添加工作表名称列，用于标识数据来源
                        df['_工作表'] = sheet_name
                        all_dataframes.append(df)
                        logger.info(f"工作表 {sheet_name} 数据已添加到合并列表")
                    
                except Exception as sheet_error:
                    logger.error(f"处理工作表 {sheet_name} 时发生错误: {sheet_error}")
                    continue
            
            if not all_dataframes:
                logger.warning("没有成功读取到任何工作表数据")
                return []
            
            # 合并所有数据框
            if len(all_dataframes) == 1:
                combined_df = all_dataframes[0]
            else:
                # 使用concat合并，忽略索引
                combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
            
            logger.info(f"合并后的数据: {combined_df.shape[0]}行 x {combined_df.shape[1]}列")
            
            # 将DataFrame转换为CSV格式的字符串
            csv_buffer = StringIO()
            combined_df.to_csv(csv_buffer, index=False, encoding='utf-8')
            csv_content = csv_buffer.getvalue()
            
            logger.info("Excel数据已成功转换为CSV格式")
            logger.info(f"CSV内容长度: {len(csv_content)} 字符")
            
            # 使用CSV处理逻辑处理转换后的数据
            csv_bytes = csv_content.encode('utf-8')
            assets = self._extract_from_csv(csv_bytes, f"{file_path}_converted.csv")
            
            logger.info(f"通过CSV转换路径提取到 {len(assets)} 个资产")
            return assets
            
        except Exception as e:
            logger.error(f"Excel转CSV处理错误: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []
    
    def _extract_from_csv(self, content: bytes, file_path: str) -> List[Dict[str, Any]]:
        """从CSV文件提取资产信息（使用智能编码检测）"""
        logger.info(f"开始解析CSV文件: {file_path}")
        
        try:
            # 直接尝试不同编码，优先处理UTF-8-BOM格式
            text_content = None
            for encoding in ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'latin1']:
                try:
                    text_content = content.decode(encoding)
                    logger.info(f"使用编码{encoding}解码成功")
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            
            if not text_content:
                logger.error("所有编码尝试均失败")
                return []
            
            # 尝试不同的CSV分隔符
            separators = [',', ';', '\t', '|']
            best_data = None
            max_columns = 0
            
            for sep in separators:
                try:
                    csv_file = StringIO(text_content)
                    reader = csv.DictReader(csv_file, delimiter=sep)
                    data = list(reader)
                    
                    if data and len(data[0]) > max_columns:
                        max_columns = len(data[0])
                        best_data = data
                        logger.info(f"使用分隔符'{sep}'解析出{len(data)}行，{max_columns}列")
                except Exception as e:
                    logger.debug(f"分隔符'{sep}'解析失败: {e}")
                    continue
            
            if not best_data:
                logger.error("无法解析CSV文件")
                return []
            
            assets = []
            for i, row in enumerate(best_data):
                asset_data = self._map_fields(row, f"CSV第{i+1}行")
                if asset_data and (asset_data.get('ip_address') or asset_data.get('hostname')):
                    assets.append(asset_data)
                    logger.info(f"成功提取资产: {asset_data.get('name', '未知设备')}")
            
            logger.info(f"CSV解析完成，总共提取 {len(assets)} 个资产")
            return assets
            
        except Exception as e:
            logger.error(f"CSV解析错误: {str(e)}")
            return []
    
    def _extract_from_text_file(self, content: bytes, file_path: str) -> List[Dict[str, Any]]:
        """从文本文件提取资产信息（使用智能编码检测）"""
        logger.info(f"开始解析文本文件: {file_path}")
        
        try:
            # 使用智能编码检测读取文本内容
            text_content, error = self.encoding_detector.read_file_content_from_bytes(content)
            if not text_content:
                logger.error(f"读取文本内容失败: {error}")
                return []
            
            logger.info(f"成功读取文本内容，长度: {len(text_content)} 字符")
            return self._extract_from_text(text_content)
            
        except Exception as e:
            logger.error(f"文本文件解析错误: {str(e)}")
            return []
    
    def _extract_from_json_file(self, content: bytes, file_path: str) -> List[Dict[str, Any]]:
        """从JSON文件提取资产信息"""
        logger.info(f"开始解析JSON文件: {file_path}")
        
        try:
            # 使用智能编码检测
            text_content, error = self.encoding_detector.read_file_content_from_bytes(content)
            if not text_content:
                logger.error(f"读取JSON内容失败: {error}")
                return []
            
            data = json.loads(text_content)
            assets = []
            
            if isinstance(data, list):
                # 直接是资产数组
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        asset_data = self._map_fields(item, f"JSON第{i+1}项")
                        if asset_data and (asset_data.get('ip_address') or asset_data.get('hostname')):
                            assets.append(asset_data)
            elif isinstance(data, dict):
                # 检查是否包含assets数组字段
                if 'assets' in data and isinstance(data['assets'], list):
                    logger.info(f"检测到包含assets数组的JSON结构，共{len(data['assets'])}个资产")
                    for i, item in enumerate(data['assets']):
                        if isinstance(item, dict):
                            logger.info(f"处理Assets数组第{i+1}项: {list(item.keys())}")
                            asset_data = self._map_fields(item, f"Assets数组第{i+1}项")
                            if asset_data:
                                logger.info(f"映射结果: {asset_data}")
                                # 更严格的验证：必须有name或ip_address
                                if asset_data.get('name') or asset_data.get('ip_address'):
                                    assets.append(asset_data)
                                    logger.info(f"添加资产: {asset_data.get('name', asset_data.get('ip_address'))}")
                                else:
                                    logger.warning(f"跳过无效资产 (缺少name和ip_address): {asset_data}")
                            else:
                                logger.warning(f"映射失败的项: {item}")
                else:
                    # 检查其他可能的数组字段名
                    array_fields = ['items', 'data', 'devices', 'nodes', 'hosts', 'servers']
                    found_array = False
                    
                    for field in array_fields:
                        if field in data and isinstance(data[field], list):
                            logger.info(f"检测到包含{field}数组的JSON结构，共{len(data[field])}个资产")
                            for i, item in enumerate(data[field]):
                                if isinstance(item, dict):
                                    asset_data = self._map_fields(item, f"{field}数组第{i+1}项")
                                    if asset_data and (asset_data.get('ip_address') or asset_data.get('hostname')):
                                        assets.append(asset_data)
                            found_array = True
                            break
                    
                    if not found_array:
                        # 将根对象当作单个资产处理
                        asset_data = self._map_fields(data, "JSON根对象")
                        if asset_data and (asset_data.get('ip_address') or asset_data.get('hostname')):
                            assets.append(asset_data)
            
            logger.info(f"JSON解析完成，总共提取 {len(assets)} 个资产")
            return assets
            
        except Exception as e:
            logger.error(f"JSON解析错误: {str(e)}")
            return []
    
    def _extract_from_text(self, content: str) -> List[Dict[str, Any]]:
        """从文本内容提取资产信息"""
        assets = []
        lines = content.split('\n')
        
        logger.info(f"开始从文本提取资产信息，共{len(lines)}行")
        
        # 先尝试检测是否为表格格式文本
        table_assets = self._extract_from_table_text(content)
        if table_assets:
            logger.info(f"从表格文本提取到 {len(table_assets)} 个资产")
            return table_assets
        
        # 查找IP地址和相关信息
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 检查是否包含IP地址
            ip_matches = self.ip_pattern.findall(line)
            if ip_matches:
                for ip in ip_matches:
                    asset_data = {'ip_address': ip}
                    
                    # 尝试从同一行提取其他信息
                    self._extract_from_line(line, asset_data)
                    
                    # 尝试从前后几行提取相关信息
                    self._extract_context_info(lines, i, asset_data)
                    
                    # 设置默认值
                    asset_data.setdefault('name', asset_data.get('hostname') or f'Device-{ip}')
                    asset_data.setdefault('asset_type', AssetType.SERVER.value)
                    asset_data.setdefault('status', AssetStatus.ACTIVE.value)
                    asset_data.setdefault('confidence_score', 75)
                    
                    assets.append(asset_data)
                    logger.info(f"从IP地址提取资产: {asset_data.get('name')}")
        
        logger.info(f"文本解析完成，总共提取 {len(assets)} 个资产")
        return assets
    
    def _map_fields(self, row_data: Dict[str, Any], context: str = "") -> Dict[str, Any]:
        """映射字段到标准格式（增强版）"""
        asset_data = {}
        
        print(f"[DEBUG] 开始映射字段 [{context}]: {row_data}")
        logger.debug(f"开始映射字段 [{context}]: {row_data}")
        
        # 清理数据
        cleaned_data = {}
        for key, value in row_data.items():
            if value is not None and value != '':
                cleaned_key = str(key).strip().lower()
                
                # 对于不同类型的值，采用不同的处理策略
                if isinstance(value, (int, float, bool)):
                    # 数值和布尔值保持原样
                    cleaned_data[cleaned_key] = value
                elif isinstance(value, list):
                    # 列表类型（如tags）保持原样
                    cleaned_data[cleaned_key] = value
                elif isinstance(value, str):
                    # 字符串类型需要去除空白并检查有效性
                    cleaned_value = value.strip()
                    if cleaned_value and cleaned_value.lower() not in ['nan', 'null', 'none', '']:
                        cleaned_data[cleaned_key] = cleaned_value
                elif pd.notna(value):
                    # 其他类型转为字符串处理
                    cleaned_value = str(value).strip()
                    if cleaned_value and cleaned_value.lower() not in ['nan', 'null', 'none', '']:
                        cleaned_data[cleaned_key] = cleaned_value
        
        logger.debug(f"清理后的数据 [{context}]: {cleaned_data}")
        
        # 字段映射 - 改进版（优先精确匹配，减少误匹配）
        mapped_fields = {}
        used_keys = set()  # 跟踪已使用的源字段，避免重复映射
        
        # 特殊处理：对于JSON格式，优先进行标准字段名的直接映射
        if "JSON" in context or "Assets" in context:
            direct_mappings = {
                'name': 'name',
                'asset_type': 'type', 
                'device_model': 'model',
                'ip_address': 'ip',
                'hostname': 'hostname',
                'username': 'username',
                'password': 'password',
                'network_location': 'network_location',
                'department': 'department',
                'status': 'status',
                'notes': 'notes',
                'tags': 'tags'
            }
            
            for source_field, target_mapping in direct_mappings.items():
                if source_field in cleaned_data and source_field not in used_keys:
                    mapped_fields[target_mapping] = cleaned_data[source_field]
                    used_keys.add(source_field)
                    logger.debug(f"JSON直接映射字段 [{context}]: {source_field} -> {target_mapping} = {cleaned_data[source_field]}")
        
        # 第一轮：精确匹配（对未直接映射的字段）
        for standard_field, possible_names in self.field_mappings.items():
            if standard_field in mapped_fields:
                continue  # 已经直接映射过了
                
            for name in possible_names:
                name_lower = name.lower()
                if name_lower in cleaned_data and name_lower not in used_keys:
                    mapped_fields[standard_field] = cleaned_data[name_lower]
                    used_keys.add(name_lower)
                    logger.debug(f"精确匹配字段 [{context}]: {name_lower} -> {standard_field} = {cleaned_data[name_lower]}")
                    break
        
        # 第二轮：模糊匹配（仅对未匹配的字段）
        for standard_field, possible_names in self.field_mappings.items():
            if standard_field in mapped_fields:
                continue  # 已经有匹配结果，跳过
                
            for name in possible_names:
                name_lower = name.lower()
                for key in cleaned_data.keys():
                    if key not in used_keys and len(name_lower) > 2:  # 避免过短的关键词误匹配
                        if (name_lower in key and len(name_lower) >= len(key) * 0.6) or \
                           (key in name_lower and len(key) >= len(name_lower) * 0.6):
                            mapped_fields[standard_field] = cleaned_data[key]
                            used_keys.add(key)
                            logger.debug(f"模糊匹配字段 [{context}]: {key} -> {standard_field} = {cleaned_data[key]}")
                            break
                if standard_field in mapped_fields:
                    break
        
        logger.debug(f"映射结果 [{context}]: {mapped_fields}")
        
        # 处理映射的字段
        for standard_field, value in mapped_fields.items():
            if standard_field == 'ip':
                print(f"[DEBUG] 发现IP字段: {value}")
                # 从URL或复合地址中提取IP
                extracted_ip = self._extract_ip_from_value(value)
                if extracted_ip:
                    asset_data['ip_address'] = extracted_ip
                    print(f"[DEBUG] IP提取成功，设置ip_address: {extracted_ip}")
                else:
                    print(f"[DEBUG] IP提取失败: {value}")
            elif standard_field == 'name' and not asset_data.get('name'):
                asset_data['name'] = value
            elif standard_field == 'hostname':
                asset_data['hostname'] = value
            elif standard_field == 'username':
                asset_data['username'] = value
            elif standard_field == 'password':
                asset_data['password'] = value
            elif standard_field == 'port':
                try:
                    port = int(float(value))
                    if 1 <= port <= 65535:
                        asset_data['port'] = port
                except (ValueError, TypeError):
                    pass
            elif standard_field == 'type':
                asset_data['asset_type'] = self._infer_asset_type(value)
            elif standard_field == 'model':
                asset_data['device_model'] = value
            elif standard_field == 'manufacturer':
                asset_data['manufacturer'] = value
            elif standard_field == 'serial':
                asset_data['serial_number'] = value
            elif standard_field == 'location':
                asset_data['location'] = value
            elif standard_field == 'department':
                asset_data['department'] = value
            elif standard_field == 'status':
                asset_data['status'] = self._infer_status(value)
            elif standard_field == 'notes':
                asset_data['notes'] = value
            elif standard_field == 'mac':
                if self._is_valid_mac(value):
                    asset_data['mac_address'] = value
            elif standard_field == 'os':
                asset_data['os_version'] = value
            elif standard_field == 'cpu':
                asset_data['cpu'] = value
            elif standard_field == 'memory':
                asset_data['memory'] = value
            elif standard_field == 'storage':
                asset_data['storage'] = value
            elif standard_field == 'service':
                asset_data['service_name'] = value
            elif standard_field == 'purpose':
                asset_data['purpose'] = value
            elif standard_field == 'network_location':
                asset_data['network_location'] = self._infer_network_location(value)
        
        # 添加详细的调试信息
        logger.info(f"映射后的asset_data [{context}]: {asset_data}")
        
        # 设置默认值和验证 - 只有确实有内容的资产才处理
        if asset_data and (asset_data.get('ip_address') or asset_data.get('hostname') or asset_data.get('name')):
            # 确保有名称
            if not asset_data.get('name'):
                asset_data['name'] = (asset_data.get('hostname') or 
                                    f"Device-{asset_data.get('ip_address', 'Unknown')}")
            
            # 设置默认的资产类型
            if not asset_data.get('asset_type'):
                asset_data['asset_type'] = AssetType.SERVER.value
            
            # 设置默认状态
            if not asset_data.get('status'):
                asset_data['status'] = AssetStatus.ACTIVE.value
            
            # 设置默认网络位置
            if not asset_data.get('network_location'):
                asset_data['network_location'] = NetworkLocation.OFFICE.value
            
            # 设置置信度
            asset_data['confidence_score'] = 85
            
            logger.info(f"✅ 成功映射资产 [{context}]: {asset_data['name']} (IP: {asset_data.get('ip_address', 'N/A')})")
            return asset_data
        
        logger.debug(f"❌ 无法映射有效资产 [{context}]: asset_data={asset_data}, 缺少关键字段")
        return None
    
    def _extract_ip_from_value(self, value: str) -> Optional[str]:
        """从各种格式的值中提取IP地址"""
        if not value or pd.isna(value):
            return None
        
        value_str = str(value).strip()
        print(f"[DEBUG] 尝试从 '{value_str}' 提取IP")
        
        # 首先尝试直接验证是否为IP
        if self._is_valid_ip(value_str):
            return value_str
        
        # 从URL中提取IP (如: https://192.168.0.240)
        import re
        
        # 匹配URL中的IP
        url_ip_pattern = re.compile(r'https?://([0-9]{1,3}\.{1,3}\.[0-9]{1,3}\.[0-9]{1,3})')
        url_match = url_ip_pattern.search(value_str)
        if url_match:
            ip = url_match.group(1)
            if self._is_valid_ip(ip):
                print(f"[DEBUG] 从URL中提取到IP: {ip}")
                return ip
        
        # 使用通用IP模式提取
        ip_matches = self.ip_pattern.findall(value_str)
        for ip in ip_matches:
            if self._is_valid_ip(ip):
                print(f"[DEBUG] 通过模式匹配提取到IP: {ip}")
                return ip
        
        print(f"[DEBUG] 无法从 '{value_str}' 中提取有效IP")
        return None
    
    def _is_valid_ip(self, ip_str: str) -> bool:
        """验证IP地址格式"""
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False
    
    def _is_valid_mac(self, mac_str: str) -> bool:
        """验证MAC地址格式"""
        return bool(self.mac_pattern.match(mac_str))
    
    def _infer_asset_type(self, type_str: str) -> AssetType:
        """推断资产类型（增强版）"""
        type_lower = type_str.lower()
        
        if any(word in type_lower for word in ['server', '服务器', '主机', 'host']):
            return AssetType.SERVER.value
        elif any(word in type_lower for word in ['switch', 'router', '交换机', '路由器', '网络', 'network']):
            return AssetType.NETWORK.value
        elif any(word in type_lower for word in ['storage', '存储', 'nas', 'san', '存储设备']):
            return AssetType.STORAGE.value
        elif any(word in type_lower for word in ['firewall', 'security', '防火墙', '安全', '安全设备']):
            return AssetType.SECURITY.value
        elif any(word in type_lower for word in ['database', 'db', '数据库', 'mysql', 'oracle', 'postgresql']):
            return AssetType.DATABASE.value
        elif any(word in type_lower for word in ['application', 'app', '应用', '应用服务器']):
            return AssetType.APPLICATION.value
        elif any(word in type_lower for word in ['monitor', '监控', '监控设备', '监控系统']):
            return AssetType.OTHER.value
        else:
            return AssetType.OTHER.value
    
    def _infer_status(self, status_str: str) -> AssetStatus:
        """推断资产状态"""
        status_lower = status_str.lower()
        
        if any(word in status_lower for word in ['active', '活跃', '在线', '正常', '运行', '正在使用']):
            return AssetStatus.ACTIVE.value
        elif any(word in status_lower for word in ['inactive', '不活跃', '离线', '停用', '闲置']):
            return AssetStatus.INACTIVE.value
        elif any(word in status_lower for word in ['maintenance', '维护', '保养', '维修']):
            return AssetStatus.MAINTENANCE.value
        elif any(word in status_lower for word in ['retired', '报废', '退役', '淘汰']):
            return AssetStatus.RETIRED.value
        else:
            return AssetStatus.ACTIVE.value  # 默认为活跃
    
    def _infer_network_location(self, location_str: str) -> NetworkLocation:
        """推断网络位置"""
        location_lower = location_str.lower()
        
        if any(word in location_lower for word in ['office', '办公', '办公网', '办公室']):
            return NetworkLocation.OFFICE.value
        elif any(word in location_lower for word in ['datacenter', '数据中心', '机房', '服务器机房']):
            return NetworkLocation.OFFICE.value
        elif any(word in location_lower for word in ['cloud', '云', '云端', '公有云', '私有云']):
            return NetworkLocation.OFFICE.value
        elif any(word in location_lower for word in ['branch', '分支', '分公司', '分支机构']):
            return NetworkLocation.OFFICE.value
        elif any(word in location_lower for word in ['dmz', '隔离区', '非军事区']):
            return NetworkLocation.OFFICE.value
        else:
            return NetworkLocation.OFFICE.value  # 默认为办公网
    
    def _extract_from_table_text(self, content: str) -> List[Dict[str, Any]]:
        """从表格格式的文本中提取资产信息"""
        lines = content.split('\n')
        assets = []
        
        logger.info("尝试从表格文本提取资产信息")
        
        # 查找可能的表头
        header_line = None
        header_index = -1
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # 检查是否为表头（包含多个常见字段名）
            header_keywords = ['ip', 'hostname', 'host', '主机', '设备', 'device', 'server', '服务器', '名称', 'name']
            keyword_count = sum(1 for keyword in header_keywords if keyword.lower() in line.lower())
            
            if keyword_count >= 2:  # 至少包含2个关键词
                header_line = line
                header_index = i
                logger.info(f"找到表头行 (第{i+1}行): {line}")
                break
        
        if header_line and header_index >= 0:
            # 解析表头
            separators = ['\t', '|', ',', '  ', '   ', ' ']
            best_separator = None
            max_fields = 0
            
            for sep in separators:
                fields = [f.strip() for f in header_line.split(sep) if f.strip()]
                if len(fields) > max_fields:
                    max_fields = len(fields)
                    best_separator = sep
            
            if best_separator and max_fields >= 2:
                headers = [f.strip() for f in header_line.split(best_separator) if f.strip()]
                logger.info(f"解析表头成功，分隔符='{best_separator}'，字段={headers}")
                
                # 处理数据行
                for i, line in enumerate(lines[header_index + 1:], header_index + 2):
                    line = line.strip()
                    if not line or line.startswith('-') or line.startswith('='):
                        continue
                    
                    values = [v.strip() for v in line.split(best_separator) if v.strip()]
                    if len(values) >= 2:
                        row_data = {}
                        for j, value in enumerate(values[:len(headers)]):
                            if j < len(headers) and value and value != '-':
                                row_data[headers[j]] = value
                        
                        asset_data = self._map_fields(row_data, f"表格第{i}行")
                        if asset_data:
                            asset_data['confidence_score'] = 90
                            assets.append(asset_data)
        
        logger.info(f"表格文本提取完成，共提取 {len(assets)} 个资产")
        return assets
    
    def _extract_context_info(self, lines: List[str], current_index: int, asset_data: Dict[str, Any]):
        """从上下文行中提取相关信息"""
        # 检查前后3行
        for offset in range(-3, 4):
            if offset == 0:
                continue
            
            check_index = current_index + offset
            if 0 <= check_index < len(lines):
                context_line = lines[check_index].strip()
                if context_line:
                    self._extract_from_line(context_line, asset_data, is_context=True)
    
    def _extract_from_line(self, line: str, asset_data: Dict[str, Any], is_context: bool = False):
        """从单行文本中提取设备信息"""
        line_lower = line.lower()
        
        # 提取主机名
        if not is_context or not asset_data.get('hostname'):
            hostname_matches = self.hostname_pattern.findall(line)
            if hostname_matches:
                hostnames = [h[0] if isinstance(h, tuple) else h for h in hostname_matches]
                hostnames = [h for h in hostnames if not self.ip_pattern.match(h) and len(h) > 2]
                if hostnames:
                    best_hostname = max(hostnames, key=lambda x: len(x) + (10 if '.' in x else 0))
                    asset_data['hostname'] = best_hostname
        
        # 提取MAC地址
        mac_matches = self.mac_pattern.findall(line)
        if mac_matches and not asset_data.get('mac_address'):
            asset_data['mac_address'] = mac_matches[0]
        
        # 提取端口号
        port_match = re.search(r':(\d{1,5})\b', line)
        if port_match and not asset_data.get('port'):
            port = int(port_match.group(1))
            if 1 <= port <= 65535:
                asset_data['port'] = port
        
        # ... 其他提取逻辑保持不变 ...
    
    def convert_to_asset_create(self, asset_data: Dict[str, Any]) -> AssetCreate:
        """将提取的数据转换为AssetCreate对象（增强版）"""
        logger.debug(f"转换资产数据为AssetCreate: {asset_data}")
        
        # 确保必填字段存在
        if not asset_data.get('name'):
            asset_data['name'] = asset_data.get('hostname') or f"Device-{asset_data.get('ip_address', 'Unknown')}"
        
        if not asset_data.get('asset_type'):
            asset_data['asset_type'] = AssetType.SERVER
            
        # 处理网络位置
        if not asset_data.get('network_location'):
            asset_data['network_location'] = NetworkLocation.OFFICE.value
        
        # 处理资产状态
        if not asset_data.get('status'):
            asset_data['status'] = AssetStatus.ACTIVE.value
        
        # 处理标签
        if isinstance(asset_data.get('tags'), str):
            asset_data['tags'] = [tag.strip() for tag in asset_data['tags'].split(',') if tag.strip()]
        
        # 移除不在AssetCreate模型中的字段
        valid_fields = {
            'name', 'asset_type', 'device_model', 'manufacturer', 'serial_number',
            'ip_address', 'mac_address', 'hostname', 'port', 'network_location',
            'username', 'password', 'ssh_key', 'location', 'rack_position',
            'datacenter', 'os_version', 'cpu', 'memory', 'storage', 'status',
            'department', 'service_name', 'application', 'purpose', 'purchase_date',
            'warranty_expiry', 'last_maintenance', 'next_maintenance', 'notes',
            'tags', 'source_file', 'source_document_id', 'confidence_score'
        }
        
        # 过滤字段，只保留有效的
        filtered_data = {}
        for key, value in asset_data.items():
            if key in valid_fields and value is not None:
                # 对于字符串字段，确保不是空字符串
                if isinstance(value, str) and value.strip() == '':
                    continue
                filtered_data[key] = value
        
        logger.info(f"创建AssetCreate对象: {filtered_data['name']}")
        return AssetCreate(**filtered_data)