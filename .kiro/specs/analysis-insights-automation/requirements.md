# 需求文档

## 简介

InsightRadar 是一个竞品洞察系统，用于跟踪 UBA 产品（Amplitude、Mixpanel、PostHog、神策数据）的新功能、策略变化和用户反馈。本需求文档定义了四个核心功能模块的扩展：社媒数据采集、LLM 分析层、洞察层和定时任务系统。

## 术语表

- **System**: InsightRadar 竞品洞察系统
- **Social_Media_Collector**: 社交媒体数据采集器
- **Tavily_API**: Tavily 搜索 API，用于快速洞察模式
- **Apify_API**: Apify 网页抓取 API，用于深度抓取模式
- **LLM_Analyzer**: 基于 OpenAI 兼容 API 的大语言模型分析器
- **Content_Classifier**: 内容分类器，将更新分类为 feature/bug/ai/pricing/strategy
- **Tag_Generator**: 标签生成器，生成智能标签如 A/B Testing、Funnel、Session Replay 等
- **Summary_Generator**: 摘要生成器，生成内容摘要
- **Trend_Clusterer**: 趋势聚类器，识别相似内容和热点方向
- **Report_Generator**: 报告生成器，生成周报和趋势分析
- **Scheduler**: 定时任务调度器，基于 APScheduler
- **ProductUpdate**: 产品更新记录模型
- **Competitor**: 竞品信息模型
- **Weekly_Report**: 周报数据模型
- **Trend_Analysis**: 趋势分析数据模型

## 需求

### 需求 1: 社交媒体数据采集

**用户故事:** 作为产品分析师，我希望系统能够采集社交媒体上的竞品讨论和用户反馈，以便捕捉用户真实声音和舆情变化。

#### 验收标准

1. THE Social_Media_Collector SHALL 支持 Tavily_API 作为快速洞察模式的数据源
2. THE Social_Media_Collector SHALL 支持 Apify_API 作为深度抓取模式的数据源
3. WHEN 配置了关键词列表，THE Social_Media_Collector SHALL 使用这些关键词进行搜索
4. WHEN 采集到社交媒体内容，THE Social_Media_Collector SHALL 将其标准化为 ProductUpdate 格式
5. THE Social_Media_Collector SHALL 将 source_type 设置为 "social"
6. WHEN 采集的内容已存在（基于 content_hash 或 source_url），THE System SHALL 跳过该内容以避免重复
7. WHEN Tavily_API 或 Apify_API 返回错误，THE Social_Media_Collector SHALL 记录错误日志并继续处理其他数据源

### 需求 2: 内容自动分类

**用户故事:** 作为产品分析师，我希望系统能够自动将采集的内容分类，以便快速识别不同类型的竞品动态。

#### 验收标准

1. WHEN ProductUpdate 记录的 update_type 为空，THE Content_Classifier SHALL 使用 LLM_Analyzer 进行分类
2. THE Content_Classifier SHALL 将内容分类为以下类别之一：feature、bug、ai、pricing、strategy
3. THE Content_Classifier SHALL 基于 title 和 content 字段进行分类
4. WHEN LLM_Analyzer 返回有效分类结果，THE Content_Classifier SHALL 更新 ProductUpdate 的 update_type 字段
5. WHEN LLM_Analyzer 调用失败或超时，THE Content_Classifier SHALL 将 update_type 设置为 "feature" 作为默认值
6. THE Content_Classifier SHALL 在 200 毫秒内完成单条记录的分类

### 需求 3: 智能标签生成

**用户故事:** 作为产品分析师，我希望系统能够为内容生成智能标签，以便按功能领域筛选和分析竞品动态。

#### 验收标准

1. WHEN ProductUpdate 记录的 tags 字段为空，THE Tag_Generator SHALL 使用 LLM_Analyzer 生成标签
2. THE Tag_Generator SHALL 生成以下预定义标签中的零个或多个：A/B Testing、Funnel、Session Replay、AI Insights、Data Warehouse、Real-time Analytics、User Segmentation、Retention Analysis、Cohort Analysis、Product Analytics
3. THE Tag_Generator SHALL 基于 title、content 和 update_type 字段生成标签
4. WHEN LLM_Analyzer 返回有效标签列表，THE Tag_Generator SHALL 更新 ProductUpdate 的 tags 字段
5. THE Tag_Generator SHALL 返回最多 5 个标签
6. WHEN LLM_Analyzer 调用失败，THE Tag_Generator SHALL 将 tags 设置为空数组

### 需求 4: 内容摘要生成

**用户故事:** 作为产品分析师，我希望系统能够为长内容生成摘要，以便快速浏览竞品动态。

#### 验收标准

1. WHEN ProductUpdate 记录的 content 长度超过 500 字符且 summary 字段为空，THE Summary_Generator SHALL 使用 LLM_Analyzer 生成摘要
2. THE Summary_Generator SHALL 生成不超过 200 字符的摘要
3. WHEN LLM_Analyzer 返回有效摘要，THE Summary_Generator SHALL 更新 ProductUpdate 的 summary 字段
4. WHEN content 长度不超过 500 字符，THE Summary_Generator SHALL 将 content 的前 200 字符作为 summary
5. WHEN LLM_Analyzer 调用失败，THE Summary_Generator SHALL 使用 content 的前 200 字符作为 summary

### 需求 5: 趋势聚类分析

**用户故事:** 作为产品分析师，我希望系统能够识别相似内容和热点方向，以便发现竞品的战略重点。

#### 验收标准

1. WHEN 请求趋势分析，THE Trend_Clusterer SHALL 分析过去 30 天的 ProductUpdate 记录
2. THE Trend_Clusterer SHALL 使用 LLM_Analyzer 识别相似主题的内容组
3. THE Trend_Clusterer SHALL 为每个趋势组生成描述性标题
4. THE Trend_Clusterer SHALL 计算每个趋势组包含的更新数量
5. THE Trend_Clusterer SHALL 按更新数量降序返回趋势列表
6. THE Trend_Clusterer SHALL 返回最多 10 个趋势组
7. WHEN 过去 30 天的更新少于 5 条，THE Trend_Clusterer SHALL 返回空列表

### 需求 6: 自动周报生成

**用户故事:** 作为产品经理，我希望系统能够自动生成周报，以便了解过去一周的竞品动态总结。

#### 验收标准

1. WHEN 请求周报，THE Report_Generator SHALL 分析过去 7 天的 ProductUpdate 记录
2. THE Report_Generator SHALL 使用 LLM_Analyzer 生成结构化周报
3. THE Report_Generator SHALL 在周报中包含以下部分：重点更新、分类统计、竞品对比、趋势洞察
4. THE Report_Generator SHALL 按产品分组展示更新统计
5. THE Report_Generator SHALL 识别最活跃的产品
6. THE Report_Generator SHALL 识别最热门的功能类别
7. WHEN 过去 7 天没有更新，THE Report_Generator SHALL 返回空周报提示

### 需求 7: 竞品能力对比

**用户故事:** 作为产品经理，我希望系统能够生成竞品能力对比表格，以便了解各竞品在不同功能领域的覆盖情况。

#### 验收标准

1. WHEN 请求竞品对比，THE Report_Generator SHALL 分析所有活跃竞品的历史更新
2. THE Report_Generator SHALL 基于 tags 字段统计每个竞品的功能覆盖
3. THE Report_Generator SHALL 生成能力矩阵，行为竞品，列为功能标签
4. THE Report_Generator SHALL 为每个竞品-功能组合计算更新数量
5. THE Report_Generator SHALL 标识每个功能领域的领先者
6. THE Report_Generator SHALL 返回 JSON 格式的对比表格数据

### 需求 8: 洞察 API 端点

**用户故事:** 作为前端开发者，我希望有清晰的 API 端点访问洞察数据，以便在界面上展示分析结果。

#### 验收标准

1. THE System SHALL 提供 GET /api/reports/weekly 端点返回周报数据
2. THE System SHALL 提供 GET /api/trends 端点返回趋势分析数据
3. THE System SHALL 提供 GET /api/compare 端点返回竞品对比数据
4. WHEN 请求 /api/reports/weekly，THE System SHALL 在 500 毫秒内返回响应
5. WHEN 请求 /api/trends，THE System SHALL 在 500 毫秒内返回响应
6. WHEN 请求 /api/compare，THE System SHALL 在 500 毫秒内返回响应
7. WHEN API 调用失败，THE System SHALL 返回包含错误信息的 JSON 响应和适当的 HTTP 状态码

### 需求 9: 定时任务调度

**用户故事:** 作为系统管理员，我希望系统能够自动执行定时采集任务，以便保持数据的时效性。

#### 验收标准

1. THE Scheduler SHALL 使用 APScheduler 管理定时任务
2. THE Scheduler SHALL 支持配置每日自动采集时间
3. WHEN 到达配置的采集时间，THE Scheduler SHALL 触发所有活跃数据源的采集
4. THE Scheduler SHALL 在采集完成后自动触发 LLM 分析流程
5. THE Scheduler SHALL 记录每次任务执行的开始时间、结束时间和状态
6. WHEN 定时任务执行失败，THE Scheduler SHALL 记录错误日志
7. THE Scheduler SHALL 支持手动触发采集任务

### 需求 10: 任务失败重试机制

**用户故事:** 作为系统管理员，我希望系统能够自动重试失败的任务，以便提高数据采集的可靠性。

#### 验收标准

1. WHEN 数据采集任务失败，THE Scheduler SHALL 在 5 分钟后自动重试
2. THE Scheduler SHALL 最多重试 3 次
3. WHEN 重试 3 次后仍然失败，THE Scheduler SHALL 记录最终失败状态并停止重试
4. THE Scheduler SHALL 为每次重试记录日志
5. WHEN LLM_Analyzer 调用失败，THE System SHALL 在 1 分钟后重试
6. THE System SHALL 对 LLM_Analyzer 调用最多重试 2 次

### 需求 11: 数据源异常监控

**用户故事:** 作为系统管理员，我希望系统能够监控数据源的健康状态，以便及时发现和处理异常。

#### 验收标准

1. WHEN 数据源连续 3 次采集失败，THE System SHALL 将该数据源标记为异常
2. THE System SHALL 记录每个数据源的最后成功采集时间
3. WHEN 数据源超过 48 小时未成功采集，THE System SHALL 生成告警日志
4. THE System SHALL 提供 GET /api/health/sources 端点返回所有数据源的健康状态
5. THE System SHALL 在健康状态响应中包含：数据源名称、最后成功时间、连续失败次数、状态标识
6. WHEN 异常数据源恢复正常，THE System SHALL 清除异常标记并记录恢复日志

### 需求 12: LLM 分析配置

**用户故事:** 作为系统管理员，我希望能够配置 LLM 分析器的参数，以便优化分析质量和成本。

#### 验收标准

1. THE System SHALL 支持通过环境变量配置 OpenAI 兼容 API 的端点地址
2. THE System SHALL 支持通过环境变量配置 API 密钥
3. THE System SHALL 支持通过环境变量配置模型名称
4. THE System SHALL 支持通过环境变量配置请求超时时间
5. THE System SHALL 支持通过环境变量配置最大 token 数量
6. WHEN 环境变量未配置，THE System SHALL 使用合理的默认值
7. WHEN API 配置无效，THE System SHALL 在启动时记录警告日志

