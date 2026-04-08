# 实现计划：分析和洞察自动化

## 概述

本实现计划将 InsightRadar 系统扩展为具备智能分析能力的竞品洞察平台。核心功能包括：社交媒体数据采集（Tavily/Apify）、LLM 驱动的内容分析（分类、标签、摘要）、趋势识别、自动化报告生成和定时任务调度。

技术栈：Python + Flask + PostgreSQL + APScheduler + OpenAI 兼容 API

## 任务列表

- [x] 1. 扩展数据模型和数据库迁移
  - 在 models.py 中添加 DataSourceHealth 模型用于监控数据源健康状态
  - 在 models.py 中添加 TaskExecutionLog 模型用于记录任务执行历史
  - 为 ProductUpdate 表添加性能优化索引（product+publish_time, update_type+publish_time, tags GIN 索引）
  - 创建数据库迁移脚本或使用 db.create_all() 应用新模型
  - _需求: 11.2, 11.4, 9.5_

- [-] 2. 实现 LLM 分析服务核心
  - [x] 2.1 创建 services/llm_analyzer.py 实现 LLMAnalyzer 类
    - 实现 __init__ 方法，从环境变量加载 OpenAI 兼容 API 配置
    - 实现 _call_llm 内部方法，包含重试逻辑（最多 2 次，间隔 1 分钟）和错误处理
    - 实现 classify_content 方法，使用 LLM 将内容分类为 feature/bug/ai/pricing/strategy
    - 实现 generate_tags 方法，生成最多 5 个预定义标签
    - 实现 generate_summary 方法，生成不超过 200 字符的摘要
    - 实现 analyze_trends 方法，识别相似主题的内容组
    - 添加超时处理（默认 30 秒）和降级策略
    - _需求: 2.1, 2.4, 3.1, 3.4, 4.1, 4.3, 5.2, 12.1-12.6_

  - [ ]* 2.2 为 LLMAnalyzer 编写单元测试
    - 测试 Prompt 构建逻辑
    - 测试降级策略（关键词匹配分类、简单截断摘要）
    - 使用 Mock 测试 API 调用和重试逻辑
    - _需求: 2.5, 3.6, 4.5, 10.5_

- [-] 3. 实现社交媒体数据采集器
  - [x] 3.1 创建 collectors/social.py 实现 SocialMediaCollector 类
    - 继承 BaseCollector，实现 collect 方法
    - 实现 _collect_from_tavily 方法，调用 Tavily API 进行快速洞察
    - 实现 _collect_from_apify 方法，调用 Apify API 进行深度抓取
    - 支持通过环境变量配置关键词列表（SOCIAL_KEYWORDS）
    - 将采集的内容标准化为 ProductUpdate 格式，source_type 设置为 "social"
    - 实现错误处理：网络超时重试 3 次（指数退避），记录错误日志
    - _需求: 1.1-1.7_

  - [ ]* 3.2 为 SocialMediaCollector 编写集成测试
    - 使用 responses 库 Mock Tavily 和 Apify API
    - 测试成功采集场景
    - 测试重试机制和错误处理
    - 测试数据去重逻辑
    - _需求: 1.6, 1.7_

- [-] 4. 实现内容分析服务
  - [x] 4.1 创建 services/classifier.py 实现 ContentClassifier 类
    - 实现 classify_update 方法，为单条 ProductUpdate 分类
    - 实现 classify_batch 方法，批量分类更新
    - 调用 LLMAnalyzer.classify_content，更新 ProductUpdate.update_type 字段
    - 实现降级策略：LLM 失败时使用 "feature" 作为默认值
    - 确保单条分类在 200ms 内完成
    - _需求: 2.1-2.6_

  - [x] 4.2 创建 services/tagger.py 实现 TagGenerator 类
    - 定义 PREDEFINED_TAGS 常量（10 个预定义标签）
    - 实现 generate_tags 方法，为单条 ProductUpdate 生成标签
    - 实现 generate_tags_batch 方法，批量生成标签
    - 调用 LLMAnalyzer.generate_tags，更新 ProductUpdate.tags 字段
    - 限制返回最多 5 个标签
    - _需求: 3.1-3.6_

  - [x] 4.3 创建 services/summarizer.py 实现 SummaryGenerator 类
    - 实现 generate_summary 方法，为单条 ProductUpdate 生成摘要
    - 实现 generate_summaries_batch 方法，批量生成摘要
    - 仅对 content 长度超过 500 字符的记录调用 LLM
    - 对于短内容，使用前 200 字符作为摘要
    - 调用 LLMAnalyzer.generate_summary，更新 ProductUpdate.summary 字段
    - _需求: 4.1-4.5_

  - [x] 4.4 为分析服务编写单元测试
    - 测试 ContentClassifier 的分类逻辑和降级策略
    - 测试 TagGenerator 的标签生成和数量限制
    - 测试 SummaryGenerator 的长度判断和摘要生成
    - 使用 Mock LLMAnalyzer 验证调用参数
    - _需求: 2.6, 3.5, 4.4_

- [x] 5. 检查点 - 确保核心分析服务正常工作
  - 确保所有测试通过，如有问题请询问用户

- [-] 6. 实现趋势分析和报告生成
  - [x] 6.1 创建 services/trend_analyzer.py 实现 TrendAnalyzer 类
    - 实现 analyze_trends 方法，分析过去 30 天的 ProductUpdate 记录
    - 调用 LLMAnalyzer.analyze_trends 识别相似主题的内容组
    - 为每个趋势组生成描述性标题和统计信息
    - 按更新数量降序返回最多 10 个趋势组
    - 当更新少于 5 条时返回空列表
    - 实现 get_trending_tags 方法，统计热门标签
    - _需求: 5.1-5.7_

  - [-] 6.2 创建 services/report_generator.py 实现 ReportGenerator 类
    - 实现 generate_weekly_report 方法，分析过去 7 天的更新
    - 生成结构化周报，包含：重点更新、分类统计、竞品对比、趋势洞察
    - 按产品分组展示统计，识别最活跃产品和最热门类别
    - 实现 generate_comparison_matrix 方法，基于 tags 生成竞品能力对比矩阵
    - 标识每个功能领域的领先者
    - 当没有数据时返回空周报提示
    - _需求: 6.1-6.7, 7.1-7.6_

  - [ ]* 6.3 为趋势分析和报告生成编写集成测试
    - 准备测试数据（过去 7 天和 30 天的更新）
    - 测试周报生成的完整性和结构
    - 测试趋势分析的聚类逻辑
    - 测试竞品对比矩阵的准确性
    - 测试空数据场景
    - _需求: 5.7, 6.7_

- [~] 7. 实现健康监控服务
  - [ ] 7.1 创建 services/health_monitor.py 实现 HealthMonitor 类
    - 实现 record_success 方法，记录数据源采集成功
    - 实现 record_failure 方法，记录数据源采集失败
    - 实现 get_source_health 方法，返回单个数据源的健康状态
    - 实现 get_all_sources_health 方法，返回所有数据源的健康状态
    - 实现 check_stale_sources 方法，检查超过 48 小时未成功采集的数据源
    - 当数据源连续 3 次失败时标记为异常，生成告警日志
    - 将健康状态持久化到 DataSourceHealth 表
    - _需求: 11.1-11.6_

  - [ ]* 7.2 为健康监控服务编写单元测试
    - 测试成功和失败记录逻辑
    - 测试连续失败计数和异常标记
    - 测试过期数据源检测
    - 测试健康状态查询
    - _需求: 11.1, 11.3_

- [ ] 8. 实现定时任务调度器
  - [ ] 8.1 创建 scheduler.py 实现 TaskScheduler 类
    - 使用 APScheduler 的 BackgroundScheduler
    - 实现 start 方法，启动调度器
    - 实现 schedule_daily_collection 方法，配置每日自动采集任务
    - 实现 schedule_analysis_pipeline 方法，配置分析流水线任务
    - 实现 trigger_collection_manually 方法，支持手动触发采集
    - 实现 _execute_collection_task 内部方法，执行采集任务
    - 实现 _execute_analysis_task 内部方法，执行分析任务（分类、标签、摘要）
    - 实现 _record_task_execution 方法，记录任务执行历史到 TaskExecutionLog 表
    - _需求: 9.1-9.7_

  - [ ] 8.2 实现任务失败重试机制
    - 在 TaskScheduler 中添加重试逻辑：采集任务失败后 5 分钟重试，最多 3 次
    - 记录每次重试到 TaskExecutionLog
    - 3 次失败后记录最终失败状态并停止重试
    - 集成 HealthMonitor，在任务失败时调用 record_failure
    - _需求: 10.1-10.6_

  - [ ] 8.3 在 app.py 中集成 TaskScheduler
    - 在应用启动时初始化 TaskScheduler
    - 配置默认的每日采集时间（从环境变量读取，默认凌晨 2 点）
    - 确保调度器在 Flask 应用上下文中运行
    - _需求: 9.2, 9.3_

  - [ ]* 8.4 为任务调度器编写集成测试
    - 测试手动触发采集任务
    - 测试任务执行记录
    - 测试重试机制
    - 使用 Mock 避免实际执行耗时任务
    - _需求: 9.7, 10.1-10.4_

- [ ] 9. 检查点 - 确保调度和监控系统正常工作
  - 确保所有测试通过，如有问题请询问用户

- [ ] 10. 扩展 API 路由
  - [ ] 10.1 在 routes/api.py 中添加洞察相关端点
    - 实现 GET /api/reports/weekly 端点，调用 ReportGenerator.generate_weekly_report
    - 实现 GET /api/trends 端点，调用 TrendAnalyzer.analyze_trends，支持 days 查询参数
    - 实现 GET /api/compare 端点，调用 ReportGenerator.generate_comparison_matrix
    - 实现 GET /api/health/sources 端点，调用 HealthMonitor.get_all_sources_health
    - 实现 POST /api/analyze/trigger 端点，手动触发分析流水线
    - 确保所有端点在 500ms 内响应（周报、趋势、对比），健康检查在 100ms 内响应
    - 添加错误处理，返回适当的 HTTP 状态码和错误信息
    - _需求: 8.1-8.7_

  - [ ] 10.2 更新 POST /api/collect 端点
    - 在现有采集逻辑后添加自动触发 LLM 分析流程
    - 对新采集的更新调用 ContentClassifier、TagGenerator 和 SummaryGenerator
    - 集成 HealthMonitor，记录采集成功/失败状态
    - _需求: 9.4, 11.1_

  - [ ]* 10.3 为新 API 端点编写集成测试
    - 测试所有新端点的响应格式和状态码
    - 测试查询参数处理
    - 测试错误场景（无数据、API 失败等）
    - 使用 pytest-benchmark 验证性能要求
    - _需求: 8.4-8.7_

- [ ] 11. 配置管理和环境变量
  - [ ] 11.1 更新 .env.example 文件
    - 添加 Tavily API 配置：TAVILY_API_KEY, SOCIAL_KEYWORDS, SOCIAL_COLLECTION_MODE
    - 添加 Apify API 配置：APIFY_API_KEY
    - 添加 OpenAI 兼容 API 配置：OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT, OPENAI_MAX_TOKENS
    - 添加调度器配置：SCHEDULER_COLLECTION_HOUR, SCHEDULER_COLLECTION_MINUTE
    - 添加合理的默认值和注释说明
    - _需求: 12.1-12.7_

  - [ ] 11.2 在 LLMAnalyzer 中实现配置验证
    - 在 __init__ 方法中检查必需的环境变量
    - 当配置无效时记录警告日志
    - 使用合理的默认值（模型：gpt-3.5-turbo，超时：30s，最大 token：1000）
    - _需求: 12.6, 12.7_

- [ ] 12. 更新 requirements.txt
  - 添加新依赖：openai（或 requests 用于 OpenAI 兼容 API）、apscheduler、python-dotenv（如未包含）
  - 添加测试依赖：pytest-mock、responses、pytest-benchmark
  - 确保版本兼容性
  - _需求: 所有_

- [ ] 13. 文档和部署准备
  - [ ] 13.1 创建 README_ANALYSIS.md 文档
    - 说明新功能的使用方法
    - 列出所有新增的环境变量和配置选项
    - 提供 API 端点使用示例
    - 说明如何配置定时任务
    - 包含故障排查指南

  - [ ] 13.2 更新数据库迁移说明
    - 提供数据库升级步骤
    - 说明如何创建新表和索引
    - 提供回滚方案

- [ ] 14. 最终检查点 - 端到端验证
  - 运行完整的测试套件，确保所有测试通过
  - 手动测试完整的数据流：采集 → 分析 → 报告生成
  - 验证定时任务正常调度
  - 验证健康监控正常工作
  - 如有问题请询问用户

## 注意事项

- 标记 `*` 的任务为可选测试任务，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求编号，确保可追溯性
- 检查点任务用于增量验证，确保系统稳定性
- 所有 LLM 调用都通过 LLMAnalyzer 统一管理，便于维护和测试
- 优先实现核心功能，测试任务可以后续补充
- 性能要求：API 响应 < 500ms，分类 < 200ms
