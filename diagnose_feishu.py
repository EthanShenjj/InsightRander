"""
飞书配置诊断工具
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def diagnose():
    print("="*70)
    print("飞书配置诊断工具")
    print("="*70)
    
    app_id = os.getenv('FEISHU_APP_ID')
    app_secret = os.getenv('FEISHU_APP_SECRET')
    app_token = os.getenv('FEISHU_BITABLE_APP_TOKEN')
    table_id = os.getenv('FEISHU_BITABLE_TABLE_ID')
    
    print(f"\n【配置信息】")
    print(f"App ID: {app_id}")
    print(f"App Token: {app_token}")
    print(f"Table ID: {table_id}")
    print(f"App Secret: {'*' * 20}...{app_secret[-4:] if app_secret else 'None'}")
    
    # 步骤 1: 获取 tenant_access_token
    print(f"\n【步骤 1】获取 Tenant Access Token")
    try:
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {
            "app_id": app_id,
            "app_secret": app_secret
        }
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        
        if response.status_code == 200 and result.get('code') == 0:
            token = result.get('tenant_access_token')
            print(f"✓ 成功获取 Token")
            print(f"  Token: {token[:30]}...")
        else:
            print(f"✗ 获取 Token 失败")
            print(f"  响应: {result}")
            return
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return
    
    # 步骤 2: 测试获取表格信息
    print(f"\n【步骤 2】测试获取表格信息（验证 app_token 和 table_id）")
    try:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        response = requests.get(url, headers=headers)
        result = response.json()
        
        print(f"  HTTP 状态码: {response.status_code}")
        print(f"  响应代码: {result.get('code')}")
        
        if response.status_code == 200 and result.get('code') == 0:
            print(f"✓ 成功访问表格")
            table_info = result.get('data', {}).get('table', {})
            print(f"  表格名称: {table_info.get('name')}")
            print(f"  表格 ID: {table_info.get('table_id')}")
        else:
            print(f"✗ 访问表格失败")
            print(f"  完整响应: {result}")
            
            # 分析错误
            code = result.get('code')
            if code == 91403:
                print(f"\n【错误分析】91403 - Forbidden")
                print(f"  可能原因：")
                print(f"  1. app_token 或 table_id 不正确")
                print(f"  2. 应用未添加到表格的协作者")
                print(f"  3. 应用权限未生效（需要重新发布版本）")
                print(f"\n  请检查：")
                print(f"  - 多维表格 URL 格式：https://xxx.feishu.cn/base/{{app_token}}?table={{table_id}}")
                print(f"  - 当前配置的 app_token: {app_token}")
                print(f"  - 当前配置的 table_id: {table_id}")
            elif code == 99991672:
                print(f"\n【错误分析】99991672 - 权限不足")
                print(f"  需要开通权限：bitable:app, base:record:read")
            
            return
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return
    
    # 步骤 3: 测试获取表格字段
    print(f"\n【步骤 3】获取表格字段列表")
    try:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        response = requests.get(url, headers=headers)
        result = response.json()
        
        if response.status_code == 200 and result.get('code') == 0:
            print(f"✓ 成功获取字段列表")
            fields = result.get('data', {}).get('items', [])
            print(f"  字段数量: {len(fields)}")
            print(f"  字段列表:")
            for field in fields:
                print(f"    - {field.get('field_name')} ({field.get('type')})")
        else:
            print(f"✗ 获取字段失败: {result}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    # 步骤 4: 测试写入数据
    print(f"\n【步骤 4】测试写入数据")
    try:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = {
            "fields": {
                "ID": "test-diagnostic-001",
                "Product": "PostHog",
                "Title": "诊断测试数据"
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        
        print(f"  HTTP 状态码: {response.status_code}")
        print(f"  响应代码: {result.get('code')}")
        
        if response.status_code == 200 and result.get('code') == 0:
            print(f"✓ 成功写入数据！")
            print(f"  记录 ID: {result.get('data', {}).get('record', {}).get('record_id')}")
            print(f"\n✓✓✓ 飞书配置完全正常！✓✓✓")
        else:
            print(f"✗ 写入数据失败")
            print(f"  完整响应: {result}")
            
            code = result.get('code')
            if code == 91403:
                print(f"\n【最终诊断】")
                print(f"  问题：应用无法写入数据到表格")
                print(f"  解决方案：")
                print(f"  1. 确认 app_token 和 table_id 是否正确")
                print(f"  2. 在多维表格中添加应用为协作者：")
                print(f"     - 打开表格 -> 右上角 ... -> 添加协作者")
                print(f"     - 搜索应用名称或 App ID: {app_id}")
                print(f"     - 给予「可编辑」权限")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    diagnose()
