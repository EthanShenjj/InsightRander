"""
测试 Changelog 采集器
"""
from collectors.changelog_scrapers import (
    PostHogChangelogCollector,
    MixpanelChangelogCollector,
    AmplitudeChangelogCollector
)
from collectors.playwright_scrapers import SensorsDataCollector

def test_collector(collector):
    print(f"\n{'='*60}")
    print(f"Testing {collector.product_name} Changelog Collector")
    url = getattr(collector, 'changelog_url', None) or getattr(collector, 'index_url', None) or getattr(collector, 'url', None) or getattr(collector, 'rss_url', '')
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        updates = collector.collect()
        print(f"✓ Successfully collected {len(updates)} updates")
        
        if updates:
            print(f"\n最新的 3 条更新：")
            for i, update in enumerate(updates[:3], 1):
                print(f"\n{i}. {update['title']}")
                print(f"   日期: {update['publish_time']}")
                print(f"   链接: {update['source_url']}")
                print(f"   内容预览: {update['content'][:100]}...")
        else:
            print("⚠ 未采集到任何更新（可能页面是 JS 渲染的）")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    collectors = [
        PostHogChangelogCollector(),
        MixpanelChangelogCollector(),
        AmplitudeChangelogCollector(),
        SensorsDataCollector()
    ]
    
    for collector in collectors:
        test_collector(collector)
    
    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}")
