# InsightRadar 配置指南

## 基础配置

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制示例配置文件：
```bash
cp .env.example .env
```

## 可选配置

### 配置飞书多维表格同步

如果需要将数据同步到飞书多维表格，需要完成以下配置：

#### 步骤 1：创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 点击"创建企业自建应用"
3. 填写应用名称和描述

#### 步骤 2：开通权限

在应用管理页面，进入"权限管理"，开通以下权限：

**必需权限：**
- `bitable:app` - 多维表格应用权限
- `base:record:create` - 创建记录权限

**可选权限（推荐）：**
- `base:record:read` - 读取记录权限
- `base:record:update` - 更新记录权限

#### 步骤 3：获取凭证

在应用管理页面：
1. 复制 `App ID`
2. 复制 `App Secret`

#### 步骤 4：创建多维表格

1. 在飞书中创建一个新的多维表格
2. 添加以下字段：

| 字段名称 | 字段类型 | 说明 |
|---------|---------|------|
| ID | 文本 | 记录唯一标识 |
| Product | 单选 | PostHog / Mixpanel / Amplitude / 神策数据 |
| Source Type | 单选 | blog / changelog / github |
| Title | 文本 | 更新标题 |
| Summary | 多行文本 | 内容摘要 |
| Type | 单选 | feature / bug / ai / pricing / strategy |
| Source URL | 超链接 | 原文链接 |
| Publish Time | 日期 | 发布时间 |

3. 从多维表格 URL 中获取配置信息：
   ```
   https://xxx.feishu.cn/base/{app_token}?table={table_id}
   ```

#### 步骤 5：配置环境变量

编辑 `.env` 文件，填入以下信息：

```env
# 飞书配置
FEISHU_APP_ID=cli_xxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxx
FEISHU_BITABLE_APP_TOKEN=bascnxxxxxxxxxxxxx
FEISHU_BITABLE_TABLE_ID=tblxxxxxxxxxxxxx
```

#### 步骤 6：测试同步

启动应用后，点击 "Scan Sources" 按钮，如果配置正确，数据会自动同步到飞书多维表格。

**常见错误：**

1. **错误代码 99991672 - 权限不足**
   - 原因：未开通必需的权限
   - 解决：在飞书开放平台开通 `bitable:app` 和 `base:record:create` 权限

2. **错误代码 99991663 - Token 无效**
   - 原因：App Secret 错误或已过期
   - 解决：重新复制 App Secret 并更新 `.env` 文件

3. **错误代码 99991664 - 应用未安装**
   - 原因：应用未安装到企业
   - 解决：在飞书开放平台点击"版本管理与发布" -> "创建版本" -> "申请发布"

### 配置 GitHub Token（可选）

如果需要采集 GitHub 数据，需要配置 GitHub Token：

1. 访问 [GitHub Settings - Tokens](https://github.com/settings/tokens)
2. 点击 "Generate new token (classic)"
3. 选择权限：`public_repo`（只读公开仓库）
4. 复制生成的 token

编辑 `.env` 文件：
```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx
```

**不配置的影响：**
- GitHub API 限流（每小时 60 次请求）
- 可能无法获取完整的 GitHub 数据

## 启动应用

```bash
python app.py
```

访问 http://localhost:5001

## 验证配置

### 测试数据采集

```bash
python test_changelog_collectors.py
```

### 检查飞书配置

启动应用后，点击 "Scan Sources"，查看控制台输出：
- 如果看到 "Feishu sync successful"，说明配置正确
- 如果看到权限错误，按照提示开通权限

## 故障排查

### 数据采集失败

1. **PostHog 采集失败**
   - 检查网络连接
   - RSS feed 可能暂时不可用

2. **Mixpanel/Amplitude 采集失败**
   - 检查网络连接
   - 检查页面 URL 是否变化
   - 查看控制台错误信息

3. **神策数据采集失败**
   - 检查官方博客是否可访问
   - 可能需要配置代理

### 飞书同步失败

1. 检查 `.env` 配置是否正确
2. 确认权限已开通
3. 查看控制台的详细错误信息
4. 参考飞书开放平台文档：https://open.feishu.cn/document/

### 性能优化

1. **数据加载慢**
   - 使用日期范围筛选（默认近 30 天）
   - 减少采集频率

2. **数据库性能**
   - 考虑使用 PostgreSQL 替代 SQLite
   - 定期清理旧数据

## 技术支持

如遇到问题，请检查：
1. Python 版本（推荐 3.8+）
2. 依赖包版本
3. 网络连接
4. 日志输出

更多信息请参考 [README.md](README.md)
