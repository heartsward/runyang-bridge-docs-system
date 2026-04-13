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
            'name': [
                'name', 'device_name', 'hostname', 'host', '设备名', '设备名称', '主机名', '名称', '资产名称',
                'server_name', 'servername', 'device_name', 'devicename', 'asset_name', 'assetname',
                '设备主机名', '机器名', '机器名称', '主机名称', '电脑名称', 'pc_name', 'computer_name',
                'instance_name', '实例名称', '资源名称', '服务名称', '服务名', '业务系统', '系统名称',
                'title', '标题', '标识', '编号', 'asset_id', 'asset_id', 'id', '唯一标识', '设备编号'
            ],
            'ip': [
                'ip', 'ip_address', 'ip地址', 'IP地址', 'IP', 'host', '主机IP', '管理IP', '设备地址', '设备IP',
                '地址', '访问地址', '连接地址', '网络地址', '公网IP', '内网IP', '私网IP', '业务IP', '服务IP',
                'management_ip', 'mgmt_ip', 'mgt_ip', '管理地址', '远程地址', 'remote_ip', 'server_ip',
                'srv_ip', '虚IP', 'vip', 'virtual_ip', '集群IP', 'cluster_ip', '节点IP', 'node_ip',
                'web_ip', '应用IP', 'db_ip', '数据库IP', 'redis_ip', '缓存IP', 'storage_ip', '存储IP',
                'idr_id', 'ids_id', '防火墙IP', '负载均衡IP', 'lb_ip', 'keepalived_ip', 'backup_ip'
            ],
            'hostname': [
                'hostname', 'host', '主机名', '设备名', 'device_name', 'name', 'server_name', '名称',
                'servername', 'devicename', 'machine_name', 'machine_name', '机器名', '实例名', 'instance',
                '实例名称', 'node_name', 'nodename', '节点名称', 'server_hostname', '物理机名', '宿主机'
            ],
            'username': [
                'username', 'user', '用户名', '用户', 'login', 'account', '登录用户', '管理用户', '管理员',
                'login_name', 'loginname', 'user_name', 'userid', 'user_id', 'account_name', 'admin_user',
                'ssh_user', 'ssh_username', 'telnet_user', 'remote_user', '连接用户', '访问用户',
                '默认用户', '默认账号', 'service_account', '服务账号', '系统账号'
            ],
            'password': [
                'password', 'pwd', '密码', 'pass', 'passwd', '登录密码', '管理密码', '口令', 'secret',
                'login_password', 'loginpwd', 'user_password', 'userpwd', 'admin_password', 'ssh_password',
                '连接密码', '访问密码', '认证密码', '认证口令', '服务器密码', '主机密码', '默认密码'
            ],
            'port': [
                'port', '端口', 'ssh_port', 'port_num', '管理端口', 'telnet_port', '服务端口', '业务端口',
                'web_port', 'http_port', 'https_port', 'app_port', '应用端口', 'db_port', 'database_port',
                'redis_port', 'cache_port', 'storage_port', '端口号', '连接端口', '访问端口', 'listen_port',
                'server_port', 'service_port', 'default_port', '内置端口'
            ],
            'os': [
                'os', 'system', '操作系统', 'os_version', '系统版本', '系统', 'operating_system', 'os_type',
                '平台', '系统平台', 'linux版本', 'windows版本', 'centos', 'ubuntu', 'redhat', 'debian',
                'windows_server', '系统类型', '软件平台', '基础软件', 'OS版本', 'kernel', '内核版本'
            ],
            'type': [
                'type', 'device_type', '设备类型', '类型', 'category', '分类', '资产类型', 'asset_type',
                '设备分类', '资源类型', 'server_type', 'host_type', '节点类型', 'instance_type', '配置类型',
                '规格', '规格型号', '子类型', 'sub_type', '设备品种', '设备品种', '产品类型'
            ],
            'model': [
                'model', '型号', 'device_model', '设备型号', '产品型号', 'product_model', '规格型号',
                'machine_model', 'server_model', '硬件型号', '设备规格', '规格', '设备编号', '产品编号',
                'model_name', 'model_name', '设备款型', '款式', '代号', 'part_number', 'pn'
            ],
            'manufacturer': [
                'manufacturer', '厂商', '制造商', 'vendor', 'brand', '品牌', '生产厂商', '生产商家',
                'supplier', '供货商', '厂家', '制造厂商', '原始厂商', 'oem', '服务商', '服务提供商',
                '华为', '华硕', '戴尔', '惠普', 'IBM', '联想', '浪潮', 'H3C', 'TP-Link', 'Cisco', 'Juniper'
            ],
            'serial': [
                'serial', 'serial_number', 'sn', '序列号', '产品序列号', 'product_sn', '设备序列号',
                '资产编号', '资产号', 'machine_serial', 'server_serial', '硬件序列号', '出厂编号',
                '出厂序列号', '唯一序列号', 'sn_number', '序列号', '系列号', 'series_number', 'license_key',
                '授权编号', '证书编号'
            ],
            'location': [
                'location', '位置', '机房', 'datacenter', '数据中心', '所在位置', '安装位置', '机房名称',
                'idc', '服务器机房', '机房位置', '机柜位置', '机架位置', '安装地点', '部署位置', '托管机房',
                '机柜号', '机柜编号', '机架', '机架号', 'cabinet', 'rack', 'rack_no', '机房code', '站点',
                'site', 'building', '楼宇', '楼层', 'room', '办公室', '办公区'
            ],
            'department': [
                'department', '部门', 'dept', 'team', '所属部门', '管理部门', '科室', '责任部门',
                '使用部门', '维护部门', '管理部门', '业务部门', '技术部门', '运维部门', '信息中心',
                'IT部门', 'dev_dept', 'ops_dept', 'business_dept', 'bu', '业务单元', '组织', 'organization'
            ],
            'status': [
                'status', '状态', '运行状态', '设备状态', '工作状态', 'state', '使用状态', '当前状态',
                '在线状态', '启用状态', '设备运行状态', '服务状态', '在线', '离线', '在用', '停用',
                '在线', 'offline', 'online', 'active', 'inactive', 'running', 'stopped', '正常', '异常'
            ],
            'notes': [
                'notes', 'note', '备注', '说明', 'description', 'remark', '描述', '备注信息', '注释',
                'comments', 'memo', '信息', '详细信息', '补充', '补充说明', '其他', '其他信息', '补充信息',
                'extra', 'extra_info', 'additional', 'additional_info', 'remark1', 'remark2'
            ],
            'rack': [
                'rack', 'rack_position', 'u_position', '机架', '机架位置', 'U位', '机位', '机框位置',
                '机框', '框号', 'slot', '插槽', '安装位置', '安装机架', '所在机架', '机架号', '机架编号',
                ' rack_no', 'rack_id', '机位号', 'u位', 'U', '高度位置', 'unit', 'ru', '导轨位置'
            ],
            'cpu': [
                'cpu', 'processor', '处理器', 'cpu_info', 'cpu型号', '中央处理器', 'CPU型号', 'CPU信息',
                'cpu_type', 'cpu_count', 'cpu核心', '核心数', '线程数', '主频', '处理器型号', '芯片',
                '处理器信息', 'CPU配置', 'CPU数量', '物理CPU', '逻辑CPU'
            ],
            'memory': [
                'memory', 'ram', '内存', 'mem', '内存大小', '内存容量', 'RAM大小', 'RAM容量', '物理内存',
                '可用内存', '内存总量', 'mem_size', 'mem_total', 'memory_size', 'mem_info', '内存信息',
                '内存配置', '机型内存', '服务器内存', 'DDR', '内存类型', '频率'
            ],
            'storage': [
                'storage', 'disk', '存储', '磁盘', 'hdd', 'ssd', '硬盘', '存储容量', '磁盘容量', '硬盘容量',
                'disk_size', 'disk_total', 'storage_size', '存储大小', '存储总量', '磁盘大小', '总存储',
                '可用存储', 'raid', 'RAID', '阵列', '存储类型', '硬盘信息', '磁盘信息', 'SAS', 'SATA', 'NVMe'
            ],
            'mac': [
                'mac', 'mac_address', 'mac地址', 'MAC地址', 'MAC', '物理地址', '网卡地址', '网卡MAC',
                '物理网卡', '本机MAC', 'host_mac', 'server_mac', '适配器地址', 'NIC', 'ethernet_mac',
                'wlana_mac', 'wwan_mac', 'b_mac', 'bridge_mac'
            ],
            'service': [
                'service', '服务', 'application', '应用', '业务', '服务名', '应用系统', '业务系统',
                '服务名称', '中间件', '数据库', 'web服务', 'http服务', 'ftp服务', 'mail服务', 'dns服务',
                'proxy服务', '负载均衡', '缓存服务', '消息队列', '日志服务', '监控服务', '存储服务'
            ],
            'purpose': [
                'purpose', '用途', '业务用途', '使用用途', 'usage', '应用场景', '使用场景', '使用说明',
                '功能', '功能说明', '业务功能', '服务内容', '应用目的', '部署目的', '作用', '职责'
            ],
            'purchase_date': [
                'purchase_date', '采购日期', '购买日期', 'buy_date', '购置日期', '入账日期', '入库日期',
                '到货日期', '验收日期', '启用日期', '投运日期', '上线日期', '投产日期', '开始使用日期',
                '部署时间', '部署日期', '上线时间', '投运时间', '进场时间', '安装时间', '进场日期'
            ],
            'warranty': [
                'warranty', 'warranty_expiry', '保修期', '质保期', '保修到期', '质保到期', '维保到期',
                '维保到期时间', 'warranty_period', 'warranty_start', '保修开始', '质保开始', '保修截止', '质保截止',
                'warranty_end', 'maintenance_expiry', '维护到期', '服务到期', 'license_expiry', '授权到期',
                '授权到期时间', '维保截止', '质保截止时间'
            ],
            'network_location': [
                'network_location', '网络位置', '网络区域', '网络环境', '所属网络', '网段', 'vlan',
                'VLAN', '子网', 'subnet', '网段地址', 'IP网段', '网络类型', '区域', 'zone', '安全区域',
                'dmz', 'DMZ', '办公网络', '生产网络', '测试网络', '开发网络', '业务网络', '管理网络',
                '带外网络', 'ILO网络', 'DRAC网络', '管控网络'
            ]
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
    
    def _extract_text_from_file(self, file_path: str, file_content: bytes, file_type: str) -> str:
        """从文件中提取文本内容（供AI分析使用）"""
        logger.info(f"开始提取文件文本内容: 文件={file_path}, 类型={file_type}, 大小={len(file_content)}字节")
        
        try:
            if file_type.lower() in ['csv', 'xlsx', 'xls']:
                from io import BytesIO, StringIO
                import pandas as pd
                
                if file_type.lower() == 'csv':
                    try:
                        text_content = file_content.decode('utf-8-sig')
                    except:
                        text_content = file_content.decode('utf-8', errors='ignore')
                    csv_buffer = StringIO(text_content)
                    df = pd.read_csv(csv_buffer)
                    text_content = df.to_string(index=False)
                    logger.info(f"CSV转换为文本，长度: {len(text_content)} 字符")
                    return text_content
                else:
                    excel_file = BytesIO(file_content)
                    engine = 'xlrd' if file_type.lower() == 'xls' else 'openpyxl'
                    try:
                        df = pd.read_excel(excel_file, engine=engine)
                        text_content = df.to_string(index=False)
                        logger.info(f"Excel转换为文本，长度: {len(text_content)} 字符")
                        return text_content
                    except Exception as e:
                        logger.warning(f"Excel读取失败: {e}")
                        return ""
            
            elif file_type.lower() in ['txt', 'md', 'json']:
                text_content, error = self.encoding_detector.read_file_content_from_bytes(file_content)
                if not text_content:
                    logger.error(f"读取文本内容失败: {error}")
                    return ""
                logger.info(f"成功读取文本内容，长度: {len(text_content)} 字符")
                return text_content
            
            else:
                text_content, error = self.encoding_detector.read_file_content_from_bytes(file_content)
                if not text_content:
                    logger.error(f"读取文件内容失败: {error}")
                    return ""
                return text_content
                
        except Exception as e:
            logger.error(f"提取文件文本内容失败: {str(e)}")
            return ""
    
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
                    # 检查其他可能的数组字段名（扩展版）
                    array_fields = [
                        'items', 'data', 'devices', 'nodes', 'hosts', 'servers', 'assets', 'records', 'list',
                        'device_list', 'server_list', 'host_list', 'inventory', 'machine_list', 'equipment',
                        'devices_info', 'servers_info', 'hosts_info', 'vm_list', 'virtual_machines', 'vms',
                        'physical_servers', 'network_devices', 'storage_devices', 'security_devices',
                        'results', 'output', 'content', 'entries', 'rows', 'records', 'info', 'details'
                    ]
                    found_array = False
                    
                    for field in array_fields:
                        if field in data and isinstance(data[field], list) and len(data[field]) > 0:
                            logger.info(f"检测到包含{field}数组的JSON结构，共{len(data[field])}个资产")
                            for i, item in enumerate(data[field]):
                                if isinstance(item, dict):
                                    asset_data = self._map_fields(item, f"{field}数组第{i+1}项")
                                    # 放宽验证条件：只要有任何有效字段即可
                                    if asset_data and any([
                                        asset_data.get('name'),
                                        asset_data.get('ip_address'),
                                        asset_data.get('hostname'),
                                        asset_data.get('device_name'),
                                        asset_data.get('serial_number'),
                                        asset_data.get('mac_address'),
                                        asset_data.get('device_model'),
                                        asset_data.get('manufacturer')
                                    ]):
                                        assets.append(asset_data)
                            found_array = True
                            break
                    
                    # 如果仍然没有找到数组，尝试遍历所有值查找数组
                    if not found_array:
                        for key, value in data.items():
                            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                                # 检查这个数组的键是否包含设备相关信息
                                first_item = value[0]
                                if any(k in str(first_item.keys()).lower() for k in ['name', 'ip', 'host', 'device', 'server', 'mac']):
                                    logger.info(f"通过内容分析检测到数组字段: {key}")
                                    for i, item in enumerate(value):
                                        if isinstance(item, dict):
                                            asset_data = self._map_fields(item, f"{key}数组第{i+1}项")
                                            if asset_data:
                                                assets.append(asset_data)
                                    found_array = True
                                    break
                    
                    if not found_array:
                        # 将根对象当作单个资产处理
                        asset_data = self._map_fields(data, "JSON根对象")
                        if asset_data:
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
                # 跳过废弃和机柜图工作表
                if '废弃' in sheet_name or '不用' in sheet_name or '机柜图' in sheet_name:
                    logger.info(f"跳过工作表: {sheet_name}")
                    continue
                    
                logger.info(f"读取工作表: {sheet_name}")
                
                # 每次读取时重新创建BytesIO，确保游标在开头
                excel_file = BytesIO(content)
                
                try:
                    df = None
                    read_success = False
                    
                    try:
                        df = pd.read_excel(excel_file, sheet_name=sheet_name, engine=engine, header=0)
                        first_col = str(df.columns[0]).strip() if len(df.columns) > 0 else ''
                        known_cols = ['序号', 'name', '设备', 'IP', 'ip', '用途', '型号', '网络']
                        if first_col not in known_cols:
                            logger.warning(f"列名不正确({first_col})，尝试skiprows方式")
                            df = pd.read_excel(BytesIO(content), sheet_name=sheet_name, engine=engine, skiprows=1)
                        read_success = True
                    except Exception as e1:
                        logger.warning(f"读取失败: {e1}")
                        try:
                            df = pd.read_excel(BytesIO(content), sheet_name=sheet_name, engine=engine, skiprows=1)
                            read_success = True
                        except Exception as e2:
                            logger.warning(f"skiprows=1也失败: {e2}")
                            try:
                                df = pd.read_excel(BytesIO(content), sheet_name=sheet_name, engine=engine)
                                read_success = True
                            except Exception as e3:
                                logger.error(f"所有读取方式都失败: {e3}")
                    
                    if read_success and df is not None:
                        df.columns = [str(c).strip() if pd.notna(c) else f'col_{i}' for i, c in enumerate(df.columns)]
                        df = df.dropna(axis=1, how='all')
                        df['_工作表'] = sheet_name
                        all_dataframes.append(df)
                        logger.info(f"工作表 {sheet_name} 数据已添加到合并列表: {df.shape[0]}行 x {df.shape[1]}列")
                        
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
        """从CSV文件提取资产信息（以IP为基准，聚合属性）"""
        logger.info(f"开始解析CSV文件: {file_path}")
        
        try:
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
            
            # 以IP为键聚合资产数据
            ip_assets_map: Dict[str, Dict[str, Any]] = {}
            assets = []
            
            for i, row in enumerate(best_data):
                asset_data = self._map_fields(row, f"CSV第{i+1}行")
                if asset_data and any([
                    asset_data.get('name'),
                    asset_data.get('ip_address'),
                    asset_data.get('hostname'),
                    asset_data.get('device_name'),
                    asset_data.get('serial_number'),
                    asset_data.get('mac_address'),
                    asset_data.get('device_model'),
                    asset_data.get('manufacturer')
                ]):
                    ip_addr = asset_data.get('ip_address')
                    
                    if ip_addr:
                        if ip_addr not in ip_assets_map:
                            ip_assets_map[ip_addr] = asset_data
                            logger.info(f"发现新资产 IP={ip_addr}, name={asset_data.get('name', 'N/A')}")
                        else:
                            existing = ip_assets_map[ip_addr]
                            for key, value in asset_data.items():
                                if value and (key not in existing or not existing[key]):
                                    existing[key] = value
                            logger.debug(f"合并资产属性 IP={ip_addr}")
                    else:
                        if asset_data.get('name') or asset_data.get('hostname'):
                            assets.append(asset_data)
            
            for ip_addr, asset_data in ip_assets_map.items():
                if not asset_data.get('name'):
                    asset_data['name'] = asset_data.get('hostname') or f"Device-{ip_addr}"
                assets.append(asset_data)
            
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
                        if asset_data:
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
                                if asset_data.get('name') or asset_data.get('ip_address'):
                                    assets.append(asset_data)
                                    logger.info(f"添加资产: {asset_data.get('name', asset_data.get('ip_address'))}")
                                else:
                                    logger.warning(f"跳过无效资产 (缺少name和ip_address): {asset_data}")
                            else:
                                logger.warning(f"映射失败的项: {item}")
                else:
                    # 检查其他可能的数组字段名（扩展版）
                    array_fields = [
                        'items', 'data', 'devices', 'nodes', 'hosts', 'servers', 'assets', 'records', 'list',
                        'device_list', 'server_list', 'host_list', 'inventory', 'machine_list', 'equipment',
                        'devices_info', 'servers_info', 'hosts_info', 'vm_list', 'virtual_machines', 'vms',
                        'physical_servers', 'network_devices', 'storage_devices', 'security_devices',
                        'results', 'output', 'content', 'entries', 'rows', 'records', 'info', 'details'
                    ]
                    found_array = False
                    
                    for field in array_fields:
                        if field in data and isinstance(data[field], list) and len(data[field]) > 0:
                            logger.info(f"检测到包含{field}数组的JSON结构，共{len(data[field])}个资产")
                            for i, item in enumerate(data[field]):
                                if isinstance(item, dict):
                                    asset_data = self._map_fields(item, f"{field}数组第{i+1}项")
                                    if asset_data and any([
                                        asset_data.get('name'),
                                        asset_data.get('ip_address'),
                                        asset_data.get('hostname'),
                                        asset_data.get('device_name'),
                                        asset_data.get('serial_number'),
                                        asset_data.get('mac_address'),
                                        asset_data.get('device_model'),
                                        asset_data.get('manufacturer')
                                    ]):
                                        assets.append(asset_data)
                            found_array = True
                            break
                    
                    # 如果仍然没有找到数组，尝试遍历所有值查找数组
                    if not found_array:
                        for key, value in data.items():
                            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                                first_item = value[0]
                                if any(k in str(first_item.keys()).lower() for k in ['name', 'ip', 'host', 'device', 'server', 'mac']):
                                    logger.info(f"通过内容分析检测到数组字段: {key}")
                                    for i, item in enumerate(value):
                                        if isinstance(item, dict):
                                            asset_data = self._map_fields(item, f"{key}数组第{i+1}项")
                                            if asset_data:
                                                assets.append(asset_data)
                                    found_array = True
                                    break
                    
                    if not found_array:
                        # 将根对象当作单个资产处理
                        asset_data = self._map_fields(data, "JSON根对象")
                        if asset_data:
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
        
        cleaned_data = {}
        for key, value in row_data.items():
            if value is not None and value != '':
                cleaned_key = str(key).strip().lower()
                
                if isinstance(value, (int, float, bool)):
                    cleaned_data[cleaned_key] = value
                elif isinstance(value, list):
                    cleaned_data[cleaned_key] = value
                elif isinstance(value, str):
                    cleaned_value = value.strip()
                    if cleaned_value and cleaned_value.lower() not in ['nan', 'null', 'none', '']:
                        cleaned_data[cleaned_key] = cleaned_value
                elif pd.notna(value):
                    cleaned_value = str(value).strip()
                    if cleaned_value and cleaned_value.lower() not in ['nan', 'null', 'none', '']:
                        cleaned_data[cleaned_key] = cleaned_value
        
        logger.debug(f"清理后的数据 [{context}]: {cleaned_data}")
        
        mapped_fields = {}
        used_keys = set()
        
        # 第一轮：中文列名精确匹配（针对Excel中文表头）
        chinese_mappings = {
            'ip地址': 'ip',
            'ip': 'ip',
            '名称': 'name',
            '设备名称': 'name',
            '设备': 'name',
            '设备编号': 'asset_code',
            '序号': 'sequence',
            '用途': 'name',
            '型号': 'model',
            '设备型号': 'model',
            '产品型号': 'model',
            '序列号': 'serial',
            '设备序列号': 'serial',
            'sn': 'serial',
            '厂商': 'manufacturer',
            '制造商': 'manufacturer',
            '品牌': 'manufacturer',
            '网络': 'network_location',
            '网络位置': 'network_location',
            '登录方式': 'login_type',
            '账号': 'username',
            '用户名': 'username',
            '用户': 'username',
            '密码': 'password',
            '登录密码': 'password',
            '机柜编号': 'asset_code',
            '机柜号': 'rack',
            '机位': 'rack',
            '设备位置': 'location',
            '位置': 'location',
            '备注': 'notes',
            '备注信息': 'notes',
            '授权到期日期': 'warranty',
            '保固': 'warranty',
            '保固到期': 'warranty',
        }
        
        for chinese_key, target_field in chinese_mappings.items():
            if chinese_key in cleaned_data and chinese_key not in used_keys:
                mapped_fields[target_field] = cleaned_data[chinese_key]
                used_keys.add(chinese_key)
                logger.debug(f"中文精确匹配 [{context}]: {chinese_key} -> {target_field} = {cleaned_data[chinese_key]}")
        
        # 第二轮：标准英文字段名精确匹配
        standard_mappings = {
            'name': 'name',
            'ip_address': 'ip',
            'ipaddress': 'ip',
            'hostname': 'hostname',
            'device_name': 'name',
            'device_name': 'name',
            'model': 'model',
            'device_model': 'model',
            'manufacturer': 'manufacturer',
            'vendor': 'manufacturer',
            'serial': 'serial',
            'serial_number': 'serial',
            'sn': 'serial',
            'username': 'username',
            'user': 'username',
            'password': 'password',
            'pwd': 'password',
            'port': 'port',
            'location': 'location',
            'rack': 'rack',
            'rack_position': 'rack',
            'department': 'department',
            'network_location': 'network_location',
            'status': 'status',
            'notes': 'notes',
            'purpose': 'purpose',
            'application': 'application',
            'service': 'service',
            'service_name': 'service',
            'os_version': 'os',
            'os': 'os',
            'cpu': 'cpu',
            'memory': 'memory',
            'storage': 'storage',
            'mac_address': 'mac',
            'mac': 'mac',
            'type': 'type',
            'asset_type': 'type',
            'warranty': 'warranty',
            'warranty_expiry': 'warranty',
        }
        
        for std_key, target_field in standard_mappings.items():
            if std_key in cleaned_data and std_key not in used_keys:
                mapped_fields[target_field] = cleaned_data[std_key]
                used_keys.add(std_key)
                logger.debug(f"标准字段匹配 [{context}]: {std_key} -> {target_field} = {cleaned_data[std_key]}")
        
        # 第三轮：模糊匹配（仅对未匹配的字段，使用严格阈值）
        def calculate_similarity(s1: str, s2: str) -> float:
            return SequenceMatcher(None, s1, s2).ratio()
        
        def contains_match(key: str, name: str) -> bool:
            key_lower = key.lower()
            name_lower = name.lower()
            if name_lower in key_lower:
                return True
            key_words = key_lower.replace('_', '').replace('-', '').replace(' ', '')
            name_words = name_lower.replace('_', '').replace('-', '').replace(' ', '')
            if name_words in key_words:
                return True
            return False
        
        for standard_field, possible_names in self.field_mappings.items():
            if standard_field in mapped_fields:
                continue
                
            best_match = None
            best_similarity = 0
            
            for name in possible_names:
                name_lower = name.lower()
                for key in cleaned_data.keys():
                    if key not in used_keys and len(name_lower) >= 3 and len(key) >= 3:
                        if contains_match(key, name_lower):
                            similarity = calculate_similarity(name_lower, key)
                            if similarity >= 0.7 and similarity > best_similarity:
                                best_similarity = similarity
                                best_match = (key, cleaned_data[key])
            
            if best_match and best_similarity >= 0.7:
                mapped_fields[standard_field] = best_match[1]
                used_keys.add(best_match[0])
                logger.debug(f"模糊匹配字段 [{context}]: {best_match[0]} -> {standard_field} = {best_match[1]} (相似度: {best_similarity:.2f})")
        
        logger.debug(f"映射结果 [{context}]: {mapped_fields}")
        
        # 处理映射的字段
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
        def calculate_similarity(s1: str, s2: str) -> float:
            """计算两个字符串的相似度"""
            return SequenceMatcher(None, s1, s2).ratio()
        
        def contains_match(key: str, name: str) -> bool:
            """检查是否存在包含匹配"""
            key_lower = key.lower()
            name_lower = name.lower()
            # 完全包含
            if name_lower in key_lower:
                return True
            # 关键词包含（用于处理中文或带特殊后缀的字段）
            key_words = key_lower.replace('_', '').replace('-', '').replace(' ', '')
            name_words = name_lower.replace('_', '').replace('-', '').replace(' ', '')
            if name_words in key_words:
                return True
            # 相似度检查
            if len(name_lower) >= 3 and len(key_lower) >= 3:
                similarity = calculate_similarity(name_lower, key_lower)
                if similarity >= 0.5:  # 降低阈值到0.5，使用更智能的相似度计算
                    return True
            return False
        
        for standard_field, possible_names in self.field_mappings.items():
            if standard_field in mapped_fields:
                continue  # 已经有匹配结果，跳过
                
            best_match = None
            best_similarity = 0
            
            for name in possible_names:
                name_lower = name.lower()
                for key in cleaned_data.keys():
                    if key not in used_keys and len(name_lower) >= 2:
                        if contains_match(key, name_lower):
                            similarity = calculate_similarity(name_lower, key)
                            if similarity > best_similarity:
                                best_similarity = similarity
                                best_match = (key, cleaned_data[key])
            if best_match:
                mapped_fields[standard_field] = best_match[1]
                used_keys.add(best_match[0])
                logger.debug(f"模糊匹配字段 [{context}]: {best_match[0]} -> {standard_field} = {best_match[1]} (相似度: {best_similarity:.2f})")
        
        logger.debug(f"映射结果 [{context}]: {mapped_fields}")
        
        # 处理映射的字段
        for standard_field, value in mapped_fields.items():
            if standard_field == 'ip':
                print(f"[DEBUG] 发现IP字段: {value}")
                extracted_ip = self._extract_ip_from_value(value)
                if extracted_ip:
                    asset_data['ip_address'] = extracted_ip
                    print(f"[DEBUG] IP提取成功，设置ip_address: {extracted_ip}")
                else:
                    print(f"[DEBUG] IP提取失败: {value}")
            elif standard_field == 'name':
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
            elif standard_field == 'rack':
                asset_data['rack'] = value
            elif standard_field == 'login_type':
                pass
            elif standard_field == 'sequence':
                pass
            elif standard_field == 'asset_code':
                asset_data['asset_code'] = value
        
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
        """从表格格式的文本中提取资产信息（以IP为基准）"""
        lines = content.split('\n')
        assets = []
        
        logger.info("尝试从表格文本提取资产信息（以IP为基准）")
        
        # 查找可能的表头
        header_line = None
        header_index = -1
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            header_keywords = ['ip', 'hostname', 'host', '主机', '设备', 'device', 'server', '服务器', '名称', 'name']
            keyword_count = sum(1 for keyword in header_keywords if keyword.lower() in line.lower())
            
            if keyword_count >= 2:
                header_line = line
                header_index = i
                logger.info(f"找到表头行 (第{i+1}行): {line}")
                break
        
        if header_line and header_index >= 0:
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
                
                # 第一步：收集所有行数据，以IP为键聚合
                ip_assets_map: Dict[str, Dict[str, Any]] = {}
                
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
                        
                        # 映射字段
                        asset_data = self._map_fields(row_data, f"表格第{i}行")
                        if asset_data:
                            # 获取该行的IP作为唯一标识
                            ip_addr = asset_data.get('ip_address')
                            
                            if ip_addr:
                                # 以IP为键，聚合属性
                                if ip_addr not in ip_assets_map:
                                    ip_assets_map[ip_addr] = asset_data
                                    ip_assets_map[ip_addr]['confidence_score'] = 90
                                    logger.info(f"发现新资产 IP={ip_addr}, name={asset_data.get('name', 'N/A')}")
                                else:
                                    # 合并属性：非空属性覆盖已有属性
                                    existing = ip_assets_map[ip_addr]
                                    for key, value in asset_data.items():
                                        if value and (key not in existing or not existing[key]):
                                            existing[key] = value
                                    logger.info(f"合并资产属性 IP={ip_addr}")
                            else:
                                # 没有IP但有其他有效信息，也创建记录（用于后续处理）
                                if asset_data.get('name') or asset_data.get('hostname'):
                                    asset_data['confidence_score'] = 85
                                    assets.append(asset_data)
                
                # 第二步：将IP聚合的资产加入结果
                for ip_addr, asset_data in ip_assets_map.items():
                    if not asset_data.get('name'):
                        asset_data['name'] = asset_data.get('hostname') or f"Device-{ip_addr}"
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