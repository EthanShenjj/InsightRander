"""
测试飞书配置是否正确
"""
import os
from dotenv import load_dotenv
from services.feishu_sync import FeishuBitableSync
from utils import get_current_utc_time

load_dotenv()

def test_feishu_config():
    print("="*60)
    print("飞书配置测试")
    print("="*60)
    
    # 检查环境变量
    app_id = os.getenv('FEISHU_APP_ID')
    app_secret = os.getenv('FEISHU_APP_SECRET')
    app_token = os.getenv('FEISHU_BITABLE_APP_TOKEN')
    table_id = os.getenv('FEISHU_BITABLE_TABLE_ID')
    
    print(f"\n1. 环境变量检查：")
    print(f"   FEISHU_APP_ID: {'✓ 已配置' if app_id else '✗ 未配置'}")
    print(f"   FEISHU_APP_SECRET: {'✓ 已配置' if app_secret else '✗ 未配置'}")
    print(f"   FEISHU_BITABLE_APP_TOKEN: {'✓ 已配置' if app_token else '✗ 未配置'}")
    print(f"   FEISHU_BITABLE_TABLE_ID: {'✓ 已配置' if table_id else '✗ 未配置'}")
    
    if not all([app_id, app_secret, app_token, table_id]):
        print("\n✗ 配置不完整，请检查 .env 文件")
        return False
    
    # 测试获取 access token
    print(f"\n2. 测试获取 Access Token：")
    try:
        sync = FeishuBitableSync()
        token = sync._get_tenant_access_token()
        if token:
            print(f"   ✓ 成功获取 Access Token")
            print(f"   Token 前缀: {token[:20]}...")
        else:
            print(f"   ✗ 获取 Token 失败")
            return False
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        return False
    
    # 测试同步数据
    print(f"\n3. 测试数据同步：")
    try:
        test_data = [{
            'id': 'test-id-12345',
            'product': 'PostHog',
            'source_type': 'blog',
            'title': '测试数据 - 请忽略',
            'summary': '这是一条测试数据，用于验证飞书同步功能',
            'update_type': 'feature',
            'source_url': 'https://example.com/test',
            'publish_time': get_current_utc_time().isoformat()
        }]
        
        result = sync.bulk_sync(test_data)
        
        if result and not any('error' in r for r in result):
            print(f"   ✓ 数据同步成功！")
            print(f"   请检查飞书多维表格是否有新记录")
            return True
        else:
            print(f"   ✗ 数据同步失败")
            if result:
                print(f"   错误信息: {result}")
            return False
            
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_feishu_config()
    print("\n" + "="*60)
    if success:
        print("✓ 飞书配置测试通过！")
    else:
        print("✗ 飞书配置测试失败，请检查配置")
        print("\n常见问题：")
        print("1. 错误 91403 (Forbidden)：")
        print("   - 应用未添加到多维表格的协作者")
        print("   - 解决：打开多维表格 -> 更多 -> 协作者 -> 添加应用")
        print("\n2. 错误 99991672 (权限不足)：")
        print("   - 权限开通后需要重新获取 App Secret")
        print("   - 确认应用已安装到企业")
        print("\n3. 检查 app_token 和 table_id 是否正确")
        print("   - 从多维表格 URL 获取：")
        print("   - https://xxx.feishu.cn/base/{app_token}?table={table_id}")
    print("="*60)
