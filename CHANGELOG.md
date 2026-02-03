# 更新日志

KERAG 项目的所有重要变更都将记录在此文件中。

## [0.1.1] - 2026-02-03

### 新增

#### 搜索 API 增强
- **子树搜索**：新增 `search_under` 参数，用于将搜索范围限制在特定节点及其后代
- **排序控制**：新增 `order` 参数，支持：
  - `priority`：按相关度分数排序（默认）
  - `dfs`：按文档顺序排序（深度优先搜索）
- **高级匹配选项**：
  - `use_regex`：启用正则表达式搜索
  - `whole_word`：仅匹配完整单词
  - `case_sensitive`：区分大小写搜索

#### 章节内容预览
- 章节节点现在显示其第一个内容子节点的内容预览
- 预览长度从 50 增加到 100 个字符，以提供更好的上下文
- 第一个子节点为章节类型的章节节点显示空预览（符合预期）

#### Web UI 改进
- 搜索栏现在包含"当前子树"复选框，用于限定搜索范围
- 新增排序下拉菜单（相关度 / 文档顺序）
- 新增区分大小写、整词匹配和正则搜索的切换按钮

#### CLI 改进
- `search` 命令现在支持 `search_under` 参数用于子树搜索
- 新增 `-o/--order` 选项控制结果排序
- 搜索结果现在显示相关度分数和内容摘要

### 变更

#### API 破坏性变更
- **搜索端点**：`scope` 参数被移除，替换为 `search_under`
  - 旧：`scope: "all" | "content" | "title" | "label"`
  - 新：`search_under?: string`（用于子树限制的节点 ID）
- **响应格式**：使用 `priority` 排序时，搜索结果现在包含 `score` 字段

#### 默认行为
- `MarkdownFormatter` 默认 `display_mode` 从 `"label"` 变更为 `"full_id"`
- `API.search()` 格式化器更新为使用 `"full_id"` 模式
- 内容预览截断现在使用 `" ... ... "` 替代 `"..."` 以提高清晰度

### 修复

- **API 路由**：修复 `/api/search`（不带尾部斜杠）返回 404 错误的问题，将 `@router.get("/")` 改为 `@router.get("")`
- **TreeFormatter**：内容预览限制从 100 调整为 50 个字符以保持一致性

### 文档

- 使用新的搜索参数更新 `KERAG_API_GUIDE.md`
- 使用 `search_nodes` 方法签名变更更新 `docs/knowledge_explorer_api.md`

### 技术细节

#### 修改的文件

**核心库 (`kerag/`)**：
- `kerag/core/knowledge_explorer.py`：新增 `_get_section_content_preview()` 方法；更新预览逻辑；修改 `search_nodes()` 签名
- `kerag/core/search_nodes.py`：实现子树过滤和排序逻辑；更新 `NodeSearcher.search()` 签名
- `kerag/front/formatters.py`：`MarkdownFormatter` 现在将章节 `content_preview` 渲染为引用块
- `kerag/api.py`：更新 `search()` 方法签名和实现
- `kerag/cli.py`：使用新参数增强 `do_search()`

**Web 后端 (`kerag-web/backend/`)**：
- `app/api/routes/search.py`：更新端点参数；修复路由装饰器

**Web 前端 (`kerag-web/frontend/`)**：
- `src/components/SearchBar.vue`：新增新搜索选项的 UI 控件
- `src/api/client.ts`：更新 `search()` 方法签名
- `src/stores/app.ts`：新增搜索状态字段
- `src/locales/*.json`：新增新 UI 元素的翻译键

**MCP 服务器 (`kerag-mcp/`)**：
- `kerag_mcp/format_response.py`：`format_node_info()` 和 `format_children_preview()` 现在显示章节内容预览
- `kerag_mcp/kerag_mcp_server.py`：更新以使用新的 API 签名

### 迁移指南

#### 针对 API 用户

**旧用法（Python API）**：
```python
api.search("keyword", scope="all")
```

**新用法**：
```python
# 全局搜索（替代 scope="all"）
api.search("keyword")

# 子树搜索
api.search("keyword", search_under="module::section_label")

# 使用选项
api.search("keyword", search_under="module::section", order="dfs", use_regex=True)
```

**旧用法（HTTP API）**：
```
GET /api/search?q=keyword&scope=all
```

**新用法**：
```
GET /api/search?q=keyword
GET /api/search?q=keyword&search_under=module::section&order=dfs
```

#### 针对模块开发者

API 响应中的章节节点现在包含 `content_preview` 字段（如适用）。这是一个附加变更，不应破坏现有代码。

---

## [0.1.0] - 2026-01

### 新增
- KERAG 系统初始版本发布
- 从 Markdown 构建知识树
- 基于 Web 的知识浏览器
- 用于 AI 代理集成的 MCP 服务器
- 知识管理 CLI 工具
