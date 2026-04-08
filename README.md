# InsightRadar - 竞品情报监控系统

自动采集和监控竞品的产品更新、功能发布和技术动态。

## 功能特性

- 📡 自动采集竞品 Changelog 和产品更新
- 🎯 支持 PostHog、Mixpanel、Amplitude、神策数据等主流产品
- 📊 现代化的 Web 仪表板展示
- 📅 灵活的日期范围筛选（近7天、近30天、近90天、自定义）
- 🔄 自动同步到飞书多维表格
- 🔍 按产品和类型筛选

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件（所有配置都是可选的）：

```env
# 数据库（可选，默认使用 SQLite）
DATABASE_URL=sqlite:///insightradar_local.db

# GitHub Token（可选）
GITHUB_TOKEN=your_github_token_here

# 飞书配置（可选）
FEISHU_APP_ID=your_feishu_app_id
FEISHU_APP_SECRET=your_feishu_app_secret
FEISHU_BITABLE_APP_TOKEN=your_bitable_app_token
FEISHU_BITABLE_TABLE_ID=your_table_id
```

### 3. 启动应用

```bash
python app.py
```

访问 http://localhost:5001

### 4. 采集数据

点击界面上的 "Scan Sources" 按钮开始采集竞品数据。

## 详细配置指南

如需配置飞书同步，请查看 [配置指南](SETUP_GUIDE.md)。

**快速链接：**
- [配置飞书同步](SETUP_GUIDE.md#配置飞书多维表格同步) - 将数据同步到飞书多维表格
- [故障排查](SETUP_GUIDE.md#故障排查) - 常见问题解决方案

## 数据采集源

### PostHog
- RSS Feed: https://posthog.com/rss.xml
- 采集方式：RSS 解析
- 内容：博客文章、产品更新

### Mixpanel
- Changelog: https://docs.mixpanel.com/changelogs
- 采集方式：BeautifulSoup
- 内容：产品发布、功能更新

### Amplitude
- Releases: https://amplitude.com/releases
- 采集方式：BeautifulSoup
- 内容：产品更新、新功能

## 飞书多维表格配置

如需同步到飞书，请在飞书中创建多维表格，包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| ID | 文本 | 记录唯一标识 |
| Product | 单选 | PostHog / Mixpanel / Amplitude |
| Source Type | 单选 | blog / changelog / github |
| Title | 文本 | 更新标题 |
| Summary | 多行文本 | 内容摘要 |
| Type | 单选 | feature / bug / ai / pricing / strategy |
| Source URL | 超链接 | 原文链接 |
| Publish Time | 日期 | 发布时间 |

## 项目结构

```
InsightRadar/
├── app.py                          # Flask 应用入口
├── models.py                       # 数据模型
├── requirements.txt                # Python 依赖
├── collectors/                     # 数据采集器
│   ├── base.py                    # 基础采集器
│   ├── changelog_scrapers.py      # Changelog 采集器
│   ├── sensorsdata.py             # 神策数据采集器
│   ├── rss.py                     # RSS 采集器
│   └── github.py                  # GitHub 采集器
├── routes/                         # API 路由
│   └── api.py                     # API 端点
├── services/                       # 服务层
│   └── feishu_sync.py             # 飞书同步服务
└── static/                         # 前端资源
    ├── index.html                 # 主页面
    ├── app.js                     # 前端逻辑
    └── styles.css                 # 样式文件
```

## API 接口

### 获取更新列表
```
GET /api/updates?product=PostHog&type=feature
```

### 触发数据采集
```
POST /api/collect
```

## 测试

测试 Changelog 采集器：

```bash
python test_changelog_collectors.py
```

## 技术栈

- Backend: Flask + SQLAlchemy
- Frontend: Vanilla JavaScript
- 数据采集: BeautifulSoup + feedparser
- 数据库: SQLite（默认）/ PostgreSQL
- 集成: 飞书多维表格 API

## License

MIT
# InsightRander
