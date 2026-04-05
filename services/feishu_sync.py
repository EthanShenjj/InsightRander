import os
import requests
import json
from datetime import datetime

class FeishuBitableSync:
    def __init__(self):
        self.app_id = os.getenv('FEISHU_APP_ID')
        self.app_secret = os.getenv('FEISHU_APP_SECRET')
        self.app_token = os.getenv('FEISHU_BITABLE_APP_TOKEN')
        self.table_id = os.getenv('FEISHU_BITABLE_TABLE_ID')
        self.base_url = "https://open.feishu.cn/open-apis"
        self._tenant_access_token = None

    def _get_tenant_access_token(self):
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        self._tenant_access_token = response.json().get("tenant_access_token")
        return self._tenant_access_token

    def _map_record(self, update_data):
        """
        Maps DB record data to Feishu Bitable field structure.
        """
        # 处理超链接字段格式
        source_url = update_data.get('source_url', '')
        url_field = {
            "link": source_url,
            "text": update_data.get('title', '')[:100]  # 链接显示文本，限制长度
        } if source_url else None
        
        # 处理日期字段格式（毫秒时间戳）
        publish_time = update_data.get('publish_time')
        if publish_time:
            try:
                from datetime import datetime
                if isinstance(publish_time, str):
                    dt = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                else:
                    dt = publish_time
                timestamp = int(dt.timestamp() * 1000)
            except:
                timestamp = None
        else:
            timestamp = None
        
        fields = {
            "ID": str(update_data.get('id', '')),
            "Product": update_data.get('product', ''),
            "Source Type": update_data.get('source_type', ''),
            "Title": update_data.get('title', ''),
            "Summary": update_data.get('summary', '') or update_data.get('content', '')[:500],
            "Type": update_data.get('update_type', 'feature'),
        }
        
        # 只有当 URL 存在时才添加
        if url_field:
            fields["Source URL"] = url_field
        
        # 只有当时间戳存在时才添加
        if timestamp:
            fields["Publish Time"] = timestamp
        
        return {"fields": fields}

    def bulk_sync(self, updates_list):
        """
        Syncs multiple ProductUpdate records to Feishu Bitable using Batch Create API.
        As per doc: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/batch_create
        """
        if not updates_list:
            return None
        
        # 检查必要的配置
        if not all([self.app_id, self.app_secret, self.app_token, self.table_id]):
            print("Feishu sync skipped: Missing configuration (app_id, app_secret, app_token, or table_id)")
            return None

        if not self._tenant_access_token:
            try:
                self._get_tenant_access_token()
            except Exception as e:
                print(f"Failed to get Feishu access token: {e}")
                return None

        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/batch_create"
        headers = {
            "Authorization": f"Bearer {self._tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # Bitable batch create supports up to 1000 records per request
        # We chunk them just in case
        results = []
        for i in range(0, len(updates_list), 1000):
            chunk = updates_list[i:i+1000]
            payload = {
                "records": [self._map_record(u) for u in chunk]
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    results.append(response.json())
                    print(f"Feishu sync successful: {len(chunk)} records synced")
                else:
                    error_msg = response.text
                    print(f"Feishu Batch Sync Failed: {error_msg}")
                    
                    # 检查是否是权限问题
                    if "99991672" in error_msg or "Access denied" in error_msg:
                        print("\n⚠️  飞书权限配置提示：")
                        print("需要在飞书开放平台为应用开通以下权限：")
                        print("  - bitable:app (多维表格应用权限)")
                        print("  - base:record:create (创建记录权限)")
                        print("配置地址：https://open.feishu.cn/app")
                        print("配置完成后需要重新获取 app_secret\n")
                    
                    results.append({"error": error_msg})
            except requests.exceptions.Timeout:
                print(f"Feishu sync timeout for chunk {i//1000 + 1}")
                results.append({"error": "Request timeout"})
            except Exception as e:
                print(f"Feishu sync error: {e}")
                results.append({"error": str(e)})
                
        return results
