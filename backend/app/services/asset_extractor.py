# -*- coding: utf-8 -*-
import re
import csv
import json
import pandas as pd
from io import StringIO, BytesIO
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import ipaddress
from pathlib import Path

from app.models.asset import AssetType, AssetStatus
from app.schemas.asset import AssetCreate


class AssetExtractor:
    """设备资产信息提取器"""
    
    def __init__(self):
        self.ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        self.mac_pattern = re.compile(r'\b[0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}\b')
        self.hostname_pattern = re.compile(r'[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*')
        
        # 常见的字段映射关系
        self.field_mappings = {
            'ip': ['ip', 'ip_address', 'ip地址', 'IP地址', 'IP', 'host'],
            'hostname': ['hostname', 'host', '主机名', '设备名', 'device_name', 'name'],
            'username': ['username', 'user', '用户名', '用户', 'login', 'account'],
            'password': ['password', 'pwd', '密码', 'pass', 'passwd'],
            'port': ['port', '端口', 'ssh_port', 'port_num'],
            'os': ['os', 'system', '操作系统', 'os_version', '系统版本'],
            'type': ['type', 'device_type', '设备类型', '类型', 'category'],
            'location': ['location', '位置', '机房', 'datacenter', '数据中心'],
            'owner': ['owner', '负责人', '管理员', 'admin', 'responsible'],
            'department': ['department', '部门', 'dept', 'team'],
            'environment': ['environment', 'env', '环境', 'stage'],
            'service': ['service', '服务', 'application', '应用'],
            'model': ['model', '型号', 'device_model', '设备型号'],
            'manufacturer': ['manufacturer', '厂商', '制造商', 'vendor', 'brand'],
            'serial': ['serial', 'serial_number', '序列号', 'sn'],
            'cpu': ['cpu', 'processor', '处理器', 'cpu_info'],
            'memory': ['memory', 'ram', '内存', 'mem'],
            'storage': ['storage', 'disk', '存储', '磁盘', 'hdd', 'ssd'],
            'mac': ['mac', 'mac_address', 'mac地址', 'MAC地址', 'MAC'],
            'notes': ['notes', 'note', '备注', '说明', 'description', 'remark']
        }
    
    def extract_from_file(self, file_path: str, file_content: bytes, file_type: str) -> List[Dict[str, Any]]:
        """从文件中提取资产信息"""
        try:
            if file_type.lower() in ['csv']:
                return self._extract_from_csv(file_content)
            elif file_type.lower() in ['xlsx', 'xls']:
                return self._extract_from_excel(file_content)
            elif file_type.lower() in ['txt', 'md']:
                return self._extract_from_text(file_content.decode('utf-8'))
            elif file_type.lower() in ['json']:
                return self._extract_from_json(file_content.decode('utf-8'))
            else:
                # 尝试从文本中提取
                try:
                    text_content = file_content.decode('utf-8')
                    return self._extract_from_text(text_content)
                except UnicodeDecodeError:
                    return []
        except Exception as e:
            print(f"提取文件内容时发生错误: {str(e)}")
            return []
    
    def _extract_from_csv(self, content: bytes) -> List[Dict[str, Any]]:
        """从CSV文件提取资产信息"""
        try:
            # 尝试不同的编码
            for encoding in ['utf-8', 'gbk', 'gb2312']:
                try:
                    text_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return []
            
            csv_file = StringIO(text_content)
            reader = csv.DictReader(csv_file)
            assets = []
            
            for row in reader:
                asset_data = self._map_fields(row)
                if asset_data and (asset_data.get('ip_address') or asset_data.get('hostname')):
                    assets.append(asset_data)
            
            return assets
        except Exception as e:
            print(f"CSV解析错误: {str(e)}")
            return []
    
    def _extract_from_excel(self, content: bytes) -> List[Dict[str, Any]]:
        """从Excel文件提取资产信息"""
        try:
            excel_file = BytesIO(content)
            df = pd.read_excel(excel_file, engine='openpyxl')
            
            assets = []
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                asset_data = self._map_fields(row_dict)
                if asset_data and (asset_data.get('ip_address') or asset_data.get('hostname')):
                    assets.append(asset_data)
            
            return assets
        except Exception as e:
            print(f"Excel解析错误: {str(e)}")
            return []
    
    def _extract_from_json(self, content: str) -> List[Dict[str, Any]]:
        """从JSON文件提取资产信息"""
        try:
            data = json.loads(content)
            if isinstance(data, list):
                assets = []
                for item in data:
                    if isinstance(item, dict):
                        asset_data = self._map_fields(item)
                        if asset_data and (asset_data.get('ip_address') or asset_data.get('hostname')):
                            assets.append(asset_data)
                return assets
            elif isinstance(data, dict):
                asset_data = self._map_fields(data)
                if asset_data and (asset_data.get('ip_address') or asset_data.get('hostname')):
                    return [asset_data]
            return []
        except Exception as e:
            print(f"JSON解析错误: {str(e)}")
            return []
    
    def _extract_from_text(self, content: str) -> List[Dict[str, Any]]:
        """从文本内容提取资产信息"""
        assets = []
        lines = content.split('\n')
        
        # 先尝试检测是否为表格格式文本
        table_assets = self._extract_from_table_text(content)
        if table_assets:
            return table_assets
        
        # 查找IP地址和相关信息
        current_asset = None
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
                    asset_data.setdefault('asset_type', AssetType.SERVER)
                    asset_data.setdefault('status', AssetStatus.ACTIVE)
                    asset_data.setdefault('confidence_score', 75)
                    
                    assets.append(asset_data)
                    
            # 如果没有IP地址，但包含设备相关关键词，也尝试提取
            elif self._contains_device_keywords(line):
                asset_data = self._extract_device_from_line(line)
                if asset_data:
                    self._extract_context_info(lines, i, asset_data)
                    assets.append(asset_data)
        
        return assets
    
    def _extract_from_table_text(self, content: str) -> List[Dict[str, Any]]:
        """从表格格式的文本中提取资产信息"""
        lines = content.split('\n')
        assets = []
        
        # 查找可能的表头
        header_line = None
        header_index = -1
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # 检查是否为表头（包含多个常见字段名）
            header_keywords = ['ip', 'hostname', 'host', '主机', '设备', 'device', 'server', '服务器']
            keyword_count = sum(1 for keyword in header_keywords if keyword.lower() in line.lower())
            
            if keyword_count >= 2:  # 至少包含2个关键词
                header_line = line
                header_index = i
                break
        
        if header_line and header_index >= 0:
            # 解析表头
            # 尝试不同的分隔符
            separators = ['\t', '|', ',', ' ', '  ', '   ']
            best_separator = None
            max_fields = 0
            
            for sep in separators:
                fields = [f.strip() for f in header_line.split(sep) if f.strip()]
                if len(fields) > max_fields:
                    max_fields = len(fields)
                    best_separator = sep
            
            if best_separator and max_fields >= 2:
                headers = [f.strip() for f in header_line.split(best_separator) if f.strip()]
                
                # 处理数据行
                for line in lines[header_index + 1:]:
                    line = line.strip()
                    if not line or line.startswith('-') or line.startswith('='):
                        continue
                    
                    values = [v.strip() for v in line.split(best_separator) if v.strip()]
                    if len(values) >= 2:
                        row_data = {}
                        for j, value in enumerate(values[:len(headers)]):
                            if j < len(headers) and value and value != '-':
                                row_data[headers[j]] = value
                        
                        asset_data = self._map_fields(row_data)
                        if asset_data:
                            asset_data.setdefault('confidence_score', 85)
                            assets.append(asset_data)
        
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
    
    def _contains_device_keywords(self, line: str) -> bool:
        """检查行是否包含设备相关关键词"""
        device_keywords = [
            'server', 'host', 'node', 'machine', 'device', 'switch', 'router',
            '服务器', '主机', '设备', '机器', '交换机', '路由器', '节点'
        ]
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in device_keywords)
    
    def _extract_device_from_line(self, line: str) -> Dict[str, Any]:
        """从包含设备关键词的行中提取设备信息"""
        asset_data = {}
        
        # 提取主机名
        hostname_matches = self.hostname_pattern.findall(line)
        if hostname_matches:
            hostnames = [h[0] if isinstance(h, tuple) else h for h in hostname_matches]
            # 过滤掉明显不是主机名的内容
            valid_hostnames = []
            for hostname in hostnames:
                if (len(hostname) > 2 and 
                    not hostname.isdigit() and 
                    '.' in hostname and
                    not self.ip_pattern.match(hostname)):
                    valid_hostnames.append(hostname)
            
            if valid_hostnames:
                asset_data['hostname'] = max(valid_hostnames, key=len)
                asset_data['name'] = asset_data['hostname']
        
        if asset_data:
            self._extract_from_line(line, asset_data)
            asset_data.setdefault('asset_type', AssetType.SERVER)
            asset_data.setdefault('status', AssetStatus.ACTIVE)
            asset_data.setdefault('confidence_score', 60)
            
        return asset_data if asset_data else None
    
    def _extract_from_line(self, line: str, asset_data: Dict[str, Any], is_context: bool = False):
        """从单行文本中提取设备信息"""
        line_lower = line.lower()
        
        # 提取主机名（仅在非上下文模式或主机名不存在时）
        if not is_context or not asset_data.get('hostname'):
            hostname_matches = self.hostname_pattern.findall(line)
            if hostname_matches:
                # 过滤掉IP地址，选择最长的主机名
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
        
        # 提取用户名
        username_patterns = [
            r'user[:\s=]+(\w+)',
            r'用户[:\s=]+(\w+)',
            r'username[:\s=]+(\w+)',
            r'login[:\s=]+(\w+)'
        ]
        if not asset_data.get('username'):
            for pattern in username_patterns:
                match = re.search(pattern, line_lower)
                if match:
                    asset_data['username'] = match.group(1)
                    break
        
        # 提取负责人/管理员
        owner_patterns = [
            r'负责人[:\s=]+([^\s,，]+)',
            r'管理员[:\s=]+([^\s,，]+)',
            r'owner[:\s=]+([^\s,，]+)',
            r'admin[:\s=]+([^\s,，]+)'
        ]
        if not asset_data.get('owner'):
            for pattern in owner_patterns:
                match = re.search(pattern, line_lower)
                if match:
                    asset_data['owner'] = match.group(1)
                    break
        
        # 提取部门信息
        dept_patterns = [
            r'部门[:\s=]+([^\s,，]+)',
            r'科室[:\s=]+([^\s,，]+)', 
            r'department[:\s=]+([^\s,，]+)',
            r'dept[:\s=]+([^\s,，]+)'
        ]
        if not asset_data.get('department'):
            for pattern in dept_patterns:
                match = re.search(pattern, line_lower)
                if match:
                    asset_data['department'] = match.group(1)
                    break
        
        # 提取环境信息
        env_patterns = [
            r'环境[:\s=]+([^\s,，]+)',
            r'environment[:\s=]+([^\s,，]+)',
            r'env[:\s=]+([^\s,，]+)'
        ]
        if not asset_data.get('environment'):
            for pattern in env_patterns:
                match = re.search(pattern, line_lower)
                if match:
                    asset_data['environment'] = match.group(1)
                    break
            
            # 如果没有明确的环境信息，通过关键词推断
            if '生产' in line or 'prod' in line_lower:
                asset_data['environment'] = '生产'
            elif '测试' in line or 'test' in line_lower:
                asset_data['environment'] = '测试'
            elif '开发' in line or 'dev' in line_lower:
                asset_data['environment'] = '开发'
        
        # 提取位置信息
        location_patterns = [
            r'位置[:\s=]+([^\s,，]+)',
            r'机房[:\s=]+([^\s,，]+)',
            r'location[:\s=]+([^\s,，]+)',
            r'datacenter[:\s=]+([^\s,，]+)'
        ]
        if not asset_data.get('location'):
            for pattern in location_patterns:
                match = re.search(pattern, line_lower)
                if match:
                    asset_data['location'] = match.group(1)
                    break
        
        # 尝试识别设备类型关键词
        if not asset_data.get('asset_type') or asset_data.get('asset_type') == AssetType.SERVER:
            if any(word in line_lower for word in ['switch', '交换机']):
                asset_data['asset_type'] = AssetType.NETWORK
            elif any(word in line_lower for word in ['router', '路由器']):
                asset_data['asset_type'] = AssetType.NETWORK
            elif any(word in line_lower for word in ['database', 'db', '数据库', 'mysql', 'postgresql', 'oracle']):
                asset_data['asset_type'] = AssetType.DATABASE
            elif any(word in line_lower for word in ['storage', '存储', 'nas', 'san']):
                asset_data['asset_type'] = AssetType.STORAGE
            elif any(word in line_lower for word in ['firewall', '防火墙', 'security', '安全设备']):
                asset_data['asset_type'] = AssetType.SECURITY
            elif any(word in line_lower for word in ['server', '服务器', 'host', '主机']):
                asset_data['asset_type'] = AssetType.SERVER
        
        # 提取操作系统信息
        os_keywords = ['windows', 'linux', 'centos', 'ubuntu', 'redhat', 'debian', 'suse']
        if not asset_data.get('os_version'):
            for os_name in os_keywords:
                if os_name in line_lower:
                    # 尝试提取版本号
                    version_match = re.search(f'{os_name}[\\s]*([\\d\\.]+)', line_lower)
                    if version_match:
                        asset_data['os_version'] = f"{os_name.capitalize()} {version_match.group(1)}"
                    else:
                        asset_data['os_version'] = os_name.capitalize()
                    break
    
    def _map_fields(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """映射字段到标准格式"""
        asset_data = {}
        
        # 清理数据
        cleaned_data = {}
        for key, value in row_data.items():
            if pd.notna(value) and str(value).strip():
                cleaned_data[str(key).strip().lower()] = str(value).strip()
        
        # 字段映射
        for standard_field, possible_names in self.field_mappings.items():
            for name in possible_names:
                if name.lower() in cleaned_data:
                    value = cleaned_data[name.lower()]
                    if value and value != 'nan':
                        # 特殊处理
                        if standard_field == 'ip':
                            if self._is_valid_ip(value):
                                asset_data['ip_address'] = value
                        elif standard_field == 'port':
                            try:
                                port = int(float(value))
                                if 1 <= port <= 65535:
                                    asset_data['port'] = port
                            except (ValueError, TypeError):
                                pass
                        elif standard_field == 'type':
                            asset_data['asset_type'] = self._infer_asset_type(value)
                        elif standard_field == 'mac':
                            if self._is_valid_mac(value):
                                asset_data['mac_address'] = value
                        else:
                            # 映射到对应字段
                            field_map = {
                                'hostname': 'hostname',
                                'username': 'username',
                                'password': 'password',
                                'os': 'os_version',
                                'location': 'location',
                                'owner': 'owner',
                                'department': 'department',
                                'environment': 'environment',
                                'service': 'service_name',
                                'model': 'model',
                                'manufacturer': 'manufacturer',
                                'serial': 'serial_number',
                                'cpu': 'cpu',
                                'memory': 'memory',
                                'storage': 'storage',
                                'notes': 'notes'
                            }
                            if standard_field in field_map:
                                asset_data[field_map[standard_field]] = value
                    break
        
        # 设置默认值
        if 'ip_address' in asset_data or 'hostname' in asset_data:
            asset_data.setdefault('name', asset_data.get('hostname') or f"Device-{asset_data.get('ip_address')}")
            asset_data.setdefault('asset_type', AssetType.SERVER)
            asset_data.setdefault('status', AssetStatus.ACTIVE)
            return asset_data
        
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
        """推断资产类型"""
        type_lower = type_str.lower()
        
        if any(word in type_lower for word in ['server', '服务器']):
            return AssetType.SERVER
        elif any(word in type_lower for word in ['switch', 'router', '交换机', '路由器', '网络']):
            return AssetType.NETWORK
        elif any(word in type_lower for word in ['storage', '存储', 'nas', 'san']):
            return AssetType.STORAGE
        elif any(word in type_lower for word in ['firewall', 'security', '防火墙', '安全']):
            return AssetType.SECURITY
        elif any(word in type_lower for word in ['database', 'db', '数据库']):
            return AssetType.DATABASE
        elif any(word in type_lower for word in ['application', 'app', '应用']):
            return AssetType.APPLICATION
        else:
            return AssetType.OTHER
    
    def merge_similar_assets(self, assets: List[Dict[str, Any]], threshold: int = 80) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """合并相似的资产"""
        if not assets:
            return assets, []
        
        merged_assets = []
        merged_groups = []
        processed = set()
        
        for i, asset in enumerate(assets):
            if i in processed:
                continue
            
            similar_assets = [asset]
            similar_indices = [i]
            
            # 查找相似的资产
            for j, other_asset in enumerate(assets):
                if i != j and j not in processed:
                    similarity = self._calculate_similarity(asset, other_asset)
                    if similarity >= threshold:
                        similar_assets.append(other_asset)
                        similar_indices.append(j)
            
            # 标记为已处理
            for idx in similar_indices:
                processed.add(idx)
            
            if len(similar_assets) > 1:
                # 合并资产
                merged_asset = self._merge_assets(similar_assets)
                merged_asset['is_merged'] = True
                merged_asset['merged_from'] = similar_indices
                merged_assets.append(merged_asset)
                merged_groups.append({
                    'merged_asset': merged_asset,
                    'source_assets': similar_assets,
                    'similarity_scores': [self._calculate_similarity(asset, other) for other in similar_assets[1:]]
                })
            else:
                merged_assets.append(asset)
        
        return merged_assets, merged_groups
    
    def _calculate_similarity(self, asset1: Dict[str, Any], asset2: Dict[str, Any]) -> int:
        """计算两个资产的相似度"""
        score = 0
        total_weight = 0
        
        # 关键字段权重
        weights = {
            'ip_address': 30,
            'hostname': 25,
            'mac_address': 20,
            'serial_number': 15,
            'name': 10
        }
        
        for field, weight in weights.items():
            val1 = asset1.get(field, '').lower().strip()
            val2 = asset2.get(field, '').lower().strip()
            
            if val1 and val2:
                if val1 == val2:
                    score += weight
                else:
                    # 使用字符串相似度
                    similarity = SequenceMatcher(None, val1, val2).ratio()
                    score += weight * similarity
                total_weight += weight
            elif val1 or val2:
                # 一个有值一个没有，降低相似度
                total_weight += weight
        
        return int((score / total_weight * 100) if total_weight > 0 else 0)
    
    def _merge_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个资产为一个"""
        if not assets:
            return {}
        
        merged = assets[0].copy()
        
        # 合并策略：优先选择最完整的信息
        for asset in assets[1:]:
            for key, value in asset.items():
                if value and (not merged.get(key) or len(str(value)) > len(str(merged.get(key, '')))):
                    merged[key] = value
        
        # 合并标签
        all_tags = set()
        for asset in assets:
            tags = asset.get('tags', [])
            if isinstance(tags, list):
                all_tags.update(tags)
            elif isinstance(tags, str):
                all_tags.update([tag.strip() for tag in tags.split(',') if tag.strip()])
        
        merged['tags'] = list(all_tags)
        merged['confidence_score'] = min(95, max(asset.get('confidence_score', 100) for asset in assets))
        
        return merged
    
    def convert_to_asset_create(self, asset_data: Dict[str, Any]) -> AssetCreate:
        """将提取的数据转换为AssetCreate对象"""
        # 确保必填字段存在
        if not asset_data.get('name'):
            asset_data['name'] = asset_data.get('hostname') or f"Device-{asset_data.get('ip_address', 'Unknown')}"
        
        if not asset_data.get('asset_type'):
            asset_data['asset_type'] = AssetType.SERVER
            
        # 处理网络位置，确保使用正确的枚举值
        if not asset_data.get('network_location'):
            from app.models.asset import NetworkLocation
            asset_data['network_location'] = NetworkLocation.OFFICE
        
        # 处理资产状态
        if not asset_data.get('status'):
            asset_data['status'] = AssetStatus.ACTIVE
        
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
        
        return AssetCreate(**filtered_data)