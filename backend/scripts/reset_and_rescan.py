
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from app import app
from models import db, ProductUpdate
from services.feishu_sync import FeishuBitableSync
# 注意：这里我们手动引入 collectors
from collectors.changelog_scrapers import (
    PostHogChangelogCollector, 
    MixpanelChangelogCollector, 
    AmplitudeChangelogCollector
)
from collectors.sensorsdata import SensorsDataCollector

collectors = [
    PostHogChangelogCollector(),
    MixpanelChangelogCollector(),
    AmplitudeChangelogCollector(),
    SensorsDataCollector()
]

def clear_feishu_table(sync_service):
    """获取飞书表格所有记录并批量删除"""
    print("Step 1: Clearing Feishu Bitable...")
    
    try:
        if not sync_service._tenant_access_token:
            sync_service._get_tenant_access_token()
    except Exception as e:
        print(f"Error getting Feishu token: {e}")
        return
    
    # 1. 获取所有记录 ID
    list_url = f"{sync_service.base_url}/bitable/v1/apps/{sync_service.app_token}/tables/{sync_service.table_id}/records"
    headers = {"Authorization": f"Bearer {sync_service._tenant_access_token}"}
    
    all_record_ids = []
    page_token = None
    
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
            
        try:
            response = requests.get(list_url, headers=headers, params=params)
            data = response.json()
            
            if response.status_code != 200:
                print(f"Error fetching Feishu records: {data}")
                break
                
            items = data.get("data", {}).get("items", [])
            all_record_ids.extend([item["record_id"] for item in items])
            
            has_more = data.get("data", {}).get("has_more", False)
            page_token = data.get("data", {}).get("page_token")
            
            if not has_more:
                break
        except Exception as e:
            print(f"Error during pagination: {e}")
            break
            
    if not all_record_ids:
        print("Feishu table is already empty.")
        return

    print(f"Found {len(all_record_ids)} records in Feishu. Deleting...")
    
    # 2. 批量删除 (飞书单次支持 500 条)
    delete_url = f"{sync_service.base_url}/bitable/v1/apps/{sync_service.app_token}/tables/{sync_service.table_id}/records/batch_delete"
    
    for i in range(0, len(all_record_ids), 500):
        chunk = all_record_ids[i:i+500]
        payload = {"records": chunk}
        try:
            res = requests.post(delete_url, headers=headers, json=payload)
            if res.status_code == 200:
                print(f"Deleted {len(chunk)} records from Feishu.")
            else:
                print(f"Failed to delete chunk: {res.text}")
        except Exception as e:
            print(f"Error during deletion: {e}")

def clear_local_db():
    """清空本地数据库"""
    print("\nStep 2: Clearing Local Database...")
    with app.app_context():
        try:
            # 兼容处理
            num_deleted = ProductUpdate.query.delete()
            db.session.commit()
            print(f"Deleted {num_deleted} records from local database.")
        except Exception as e:
            print(f"Error clearing DB: {e}")
            db.session.rollback()

def rescan_and_sync():
    """重新采集并同步"""
    print("\nStep 3: Rescanning data (especially for Amplitude fixes)...")
    all_new_updates = []
    
    for collector in collectors:
        print(f"Scanning {collector.product_name}...")
        try:
            updates = collector.collect()
            all_new_updates.extend(updates)
            print(f"Found {len(updates)} updates for {collector.product_name}")
        except Exception as e:
            print(f"Error scanning {collector.product_name}: {e}")

    if not all_new_updates:
        print("No updates found during rescan.")
        return

    print(f"\nStep 4: Saving {len(all_new_updates)} new records to DB and Syncing to Feishu...")
    
    with app.app_context():
        saved_updates_data = []
        for u in all_new_updates:
            # 去重检查（以 URL 为准）
            existing = ProductUpdate.query.filter_by(source_url=u['source_url']).first()
            if not existing:
                update = ProductUpdate(
                    product=u['product'],
                    title=u['title'],
                    content=u.get('content', u['title']),
                    summary=u.get('summary', ''),
                    source_url=u['source_url'],
                    source_type=u.get('source_type', 'changelog'),
                    publish_time=u.get('publish_time'),
                    content_hash=u.get('content_hash', '')
                )
                # 使用 property 处理 JSON 序列化
                update.raw_data_dict = u.get('raw_data', {})
                
                db.session.add(update)
                db.session.flush() # 获取 ID
                
                saved_updates_data.append({
                    'id': update.id,
                    'product': update.product,
                    'title': update.title,
                    'content': update.content,
                    'summary': update.summary,
                    'source_url': update.source_url,
                    'source_type': update.source_type,
                    'publish_time': update.publish_time
                })
        
        db.session.commit()
        print(f"Saved {len(saved_updates_data)} records to local DB.")
        
        # 同步到飞书
        if saved_updates_data:
            sync_service = FeishuBitableSync()
            sync_service.bulk_sync(saved_updates_data)
            print("Sync to Feishu completed.")

if __name__ == "__main__":
    sync_service = FeishuBitableSync()
    
    # 执行全量清理
    clear_feishu_table(sync_service)
    clear_local_db()
    
    # 重新开始
    rescan_and_sync()
    
    print("\n✅ Reset and Rescan operation completed successfully!")
