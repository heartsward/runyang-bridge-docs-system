# -*- coding: utf-8 -*-
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.crud.base import CRUDBase
from app.models.asset import Asset, AssetExtractRule, AssetType, AssetStatus
from app.schemas.asset import AssetCreate, AssetUpdate, AssetSearchQuery


class CRUDAsset(CRUDBase[Asset, AssetCreate, AssetUpdate]):
    
    def get_by_ip(self, db: Session, *, ip_address: str) -> Optional[Asset]:
        """根据IP地址获取资产"""
        return db.query(Asset).filter(Asset.ip_address == ip_address).first()
    
    def get_by_hostname(self, db: Session, *, hostname: str) -> Optional[Asset]:
        """根据主机名获取资产"""
        return db.query(Asset).filter(Asset.hostname == hostname).first()
    
    def get_by_serial_number(self, db: Session, *, serial_number: str) -> Optional[Asset]:
        """根据序列号获取资产"""
        return db.query(Asset).filter(Asset.serial_number == serial_number).first()
    
    def search(self, db: Session, *, query: AssetSearchQuery) -> List[Asset]:
        """搜索资产"""
        q = db.query(Asset)
        
        # 基本搜索
        if query.query:
            search_term = f"%{query.query}%"
            q = q.filter(
                or_(
                    Asset.name.ilike(search_term),
                    Asset.hostname.ilike(search_term),
                    Asset.ip_address.ilike(search_term),
                    Asset.device_model.ilike(search_term),
                    Asset.service_name.ilike(search_term),
                    Asset.application.ilike(search_term),
                    Asset.notes.ilike(search_term)
                )
            )
        
        # 按类型过滤
        if query.asset_type:
            q = q.filter(Asset.asset_type == query.asset_type)
        
        # 按状态过滤
        if query.status:
            q = q.filter(Asset.status == query.status)
        
        # 按IP地址过滤
        if query.ip_address:
            q = q.filter(Asset.ip_address.ilike(f"%{query.ip_address}%"))
        
        # 按部门过滤
        if query.department:
            q = q.filter(Asset.department.ilike(f"%{query.department}%"))
        
        # 按网络位置过滤
        if query.network_location:
            q = q.filter(Asset.network_location == query.network_location)
        
        # 按标签过滤
        if query.tags:
            for tag in query.tags:
                q = q.filter(Asset.tags.ilike(f"%{tag}%"))
        
        # 排序和分页
        q = q.order_by(desc(Asset.updated_at))
        offset = (query.page - 1) * query.per_page
        return q.offset(offset).limit(query.per_page).all()
    
    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """获取资产统计信息"""
        total_count = db.query(Asset).count()
        
        # 按类型统计
        by_type = {}
        type_stats = db.query(Asset.asset_type, func.count(Asset.id)).group_by(Asset.asset_type).all()
        for asset_type, count in type_stats:
            by_type[asset_type.value] = count
        
        # 按状态统计
        by_status = {}
        status_stats = db.query(Asset.status, func.count(Asset.id)).group_by(Asset.status).all()
        for status, count in status_stats:
            by_status[status.value] = count
        
        # 按网络位置统计
        by_network_location = {}
        location_stats = db.query(Asset.network_location, func.count(Asset.id)).filter(
            Asset.network_location.isnot(None)
        ).group_by(Asset.network_location).all()
        for location, count in location_stats:
            by_network_location[location.value] = count
        
        # 按部门统计
        by_department = {}
        dept_stats = db.query(Asset.department, func.count(Asset.id)).filter(
            Asset.department.isnot(None)
        ).group_by(Asset.department).all()
        for dept, count in dept_stats:
            by_department[dept] = count
        
        # 最近30天新增
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_additions = db.query(Asset).filter(Asset.created_at >= thirty_days_ago).count()
        
        # 待维护数量(假设下次维护时间已过期)
        pending_maintenance = db.query(Asset).filter(
            and_(
                Asset.next_maintenance.isnot(None),
                Asset.next_maintenance <= datetime.now()
            )
        ).count()
        
        return {
            "total_count": total_count,
            "by_type": by_type,
            "by_status": by_status,
            "by_network_location": by_network_location,
            "by_department": by_department,
            "recent_additions": recent_additions,
            "pending_maintenance": pending_maintenance
        }
    
    def create_with_merge_info(self, db: Session, *, obj_in: AssetCreate, creator_id: int, merged_from: List[int] = None) -> Asset:
        """创建资产，包含合并信息"""
        from datetime import datetime
        
        obj_data = obj_in.model_dump(exclude_unset=True)
        
        # 处理标签
        if obj_data.get('tags'):
            obj_data['tags'] = json.dumps(obj_data['tags'])
        else:
            obj_data['tags'] = '[]'
        
        # 处理合并信息
        if merged_from:
            obj_data['is_merged'] = True
            obj_data['merged_from'] = json.dumps(merged_from)
        else:
            obj_data['is_merged'] = False
        
        # 设置基本字段
        obj_data['creator_id'] = creator_id
        obj_data['created_at'] = datetime.now()
        obj_data['updated_at'] = datetime.now()
        
        db_obj = Asset(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def bulk_create(self, db: Session, *, assets: List[AssetCreate], creator_id: int) -> List[Asset]:
        """批量创建资产"""
        db_assets = []
        for asset_data in assets:
            obj_data = asset_data.model_dump(exclude_unset=True)
            
            from datetime import datetime
            
            # 处理标签
            if obj_data.get('tags'):
                obj_data['tags'] = json.dumps(obj_data['tags'])
            else:
                obj_data['tags'] = '[]'
            
            # 设置基本字段
            obj_data['creator_id'] = creator_id
            obj_data['created_at'] = datetime.now()
            obj_data['updated_at'] = datetime.now()
            obj_data['is_merged'] = False
            
            db_obj = Asset(**obj_data)
            db_assets.append(db_obj)
        
        db.add_all(db_assets)
        db.commit()
        
        for db_obj in db_assets:
            db.refresh(db_obj)
        
        return db_assets
    
    def find_similar_assets(self, db: Session, *, asset: AssetCreate, threshold: int = 80) -> List[Asset]:
        """查找相似的资产"""
        similar_assets = []
        
        # 按IP地址查找
        if asset.ip_address:
            ip_matches = db.query(Asset).filter(Asset.ip_address == asset.ip_address).all()
            similar_assets.extend(ip_matches)
        
        # 按主机名查找
        if asset.hostname:
            hostname_matches = db.query(Asset).filter(Asset.hostname == asset.hostname).all()
            similar_assets.extend(hostname_matches)
        
        # 按序列号查找
        if asset.serial_number:
            serial_matches = db.query(Asset).filter(Asset.serial_number == asset.serial_number).all()
            similar_assets.extend(serial_matches)
        
        # 按MAC地址查找
        if asset.mac_address:
            mac_matches = db.query(Asset).filter(Asset.mac_address == asset.mac_address).all()
            similar_assets.extend(mac_matches)
        
        # 去重
        unique_assets = []
        seen_ids = set()
        for similar_asset in similar_assets:
            if similar_asset.id not in seen_ids:
                unique_assets.append(similar_asset)
                seen_ids.add(similar_asset.id)
        
        return unique_assets
    
    def merge_assets(self, db: Session, *, source_ids: List[int], target_asset: AssetCreate, creator_id: int) -> Asset:
        """合并多个资产"""
        # 获取源资产
        source_assets = db.query(Asset).filter(Asset.id.in_(source_ids)).all()
        
        # 创建合并后的资产
        merged_asset = self.create_with_merge_info(
            db=db,
            obj_in=target_asset,
            creator_id=creator_id,
            merged_from=source_ids
        )
        
        # 删除源资产或标记为已合并
        for source_asset in source_assets:
            source_asset.status = AssetStatus.ARCHIVED
            source_asset.notes = f"已合并到资产 #{merged_asset.id}"
        
        db.commit()
        return merged_asset
    
    def get_by_document(self, db: Session, *, document_id: int) -> List[Asset]:
        """获取从指定文档提取的资产"""
        return db.query(Asset).filter(Asset.source_document_id == document_id).all()
    
    def get_multi_by_ids(self, db: Session, *, ids: List[int]) -> List[Asset]:
        """根据ID列表获取多个资产"""
        return db.query(Asset).filter(Asset.id.in_(ids)).all()
    
    def bulk_remove(self, db: Session, *, ids: List[int]) -> int:
        """批量删除资产"""
        deleted_count = db.query(Asset).filter(Asset.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return deleted_count


class CRUDAssetExtractRule(CRUDBase[AssetExtractRule, Dict, Dict]):
    
    def get_active_rules(self, db: Session) -> List[AssetExtractRule]:
        """获取所有启用的提取规则"""
        return db.query(AssetExtractRule).filter(
            AssetExtractRule.is_active == True
        ).order_by(AssetExtractRule.priority.desc()).all()
    
    def get_by_file_type(self, db: Session, *, file_type: str) -> List[AssetExtractRule]:
        """根据文件类型获取提取规则"""
        return db.query(AssetExtractRule).filter(
            and_(
                AssetExtractRule.is_active == True,
                AssetExtractRule.file_types.ilike(f"%{file_type}%")
            )
        ).order_by(AssetExtractRule.priority.desc()).all()


# 创建实例
asset = CRUDAsset(Asset)
asset_extract_rule = CRUDAssetExtractRule(AssetExtractRule)