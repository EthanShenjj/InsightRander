"""
性能测试脚本
"""
import time
from app import app, db, ProductUpdate
from datetime import datetime, timedelta

def test_query_performance():
    with app.app_context():
        print("="*60)
        print("数据库查询性能测试")
        print("="*60)
        
        # 测试 1: 查询所有数据
        print("\n【测试 1】查询所有数据")
        start = time.time()
        all_updates = ProductUpdate.query.all()
        elapsed = time.time() - start
        print(f"  记录数: {len(all_updates)}")
        print(f"  耗时: {elapsed:.3f} 秒")
        
        # 测试 2: 按日期范围查询（近30天）
        print("\n【测试 2】查询近30天数据")
        start = time.time()
        cutoff = datetime.utcnow() - timedelta(days=30)
        recent_updates = ProductUpdate.query.filter(
            ProductUpdate.publish_time >= cutoff
        ).order_by(ProductUpdate.publish_time.desc()).limit(200).all()
        elapsed = time.time() - start
        print(f"  记录数: {len(recent_updates)}")
        print(f"  耗时: {elapsed:.3f} 秒")
        
        # 测试 3: 按产品筛选
        print("\n【测试 3】按产品筛选（PostHog）")
        start = time.time()
        posthog_updates = ProductUpdate.query.filter(
            ProductUpdate.product == 'PostHog'
        ).all()
        elapsed = time.time() - start
        print(f"  记录数: {len(posthog_updates)}")
        print(f"  耗时: {elapsed:.3f} 秒")
        
        # 测试 4: 组合查询
        print("\n【测试 4】组合查询（PostHog + 近30天）")
        start = time.time()
        combined = ProductUpdate.query.filter(
            ProductUpdate.product == 'PostHog',
            ProductUpdate.publish_time >= cutoff
        ).order_by(ProductUpdate.publish_time.desc()).limit(200).all()
        elapsed = time.time() - start
        print(f"  记录数: {len(combined)}")
        print(f"  耗时: {elapsed:.3f} 秒")
        
        print("\n" + "="*60)
        print("性能测试完成")
        print("="*60)

if __name__ == '__main__':
    test_query_performance()
