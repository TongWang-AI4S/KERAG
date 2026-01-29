# KERAG (知识探索检索增强生成) - 核心库

KERAG 是一个强大的系统，旨在将带有自定义语法的 Markdown 文件转换为分层的知识库结构，方便知识检索和 AI 驱动的探索。

## 🚀 安装

你可以直接从 GitHub 安装核心库：

```bash
pip install git+https://github.com/TongWang-AI4S/KERAG.git
```

## ✨ 核心特性

- **分层节点结构**: 将线性 Markdown 转换为可导航的节点图。
- **自定义语法**:
    - `[@label]`: 定义节点锚点。
    - `(@node_id)`: 创建交叉引用。
    - `## (@referred_node_id)`: 嵌入整个子树。
- **快速知识树构建器**: 使用 `kerag tool split` 命令自动将大型文档分割为分层知识模块。

## 🌳 快速构建知识树

使用 `kerag tool split` 命令可以快速从大型 Markdown 文档构建初步知识树：

```bash
# 在 ### 级别分割文档（默认）
kerag tool split my-document.md

# 在 ## 级别分割并输出到自定义目录
kerag tool split my-document.md -l 2 -o my-knowledge-base

# 自动为所有标题添加标签
kerag tool split my-document.md --all-labeled
```

该命令将：
- 创建带有子树引用的主 `index.md` 文件
- 为指定标题级别的每个章节生成独立文件
- 自动调整子文件中的标题层级

## 📂 知识库目录与作用域

KERAG 支持两种作用域的知识库管理，允许您灵活组织通用知识和项目特定知识：

- **全局作用域 (Global)**: 默认路径为 `~/.kerag_modules`。存放可供所有项目访问的通用知识模块。
- **局部作用域 (Local)**: 默认路径为当前工作目录下的 `./.kerag_modules`。存放仅与当前项目相关的专业知识模块。

### 环境变量配置
您可以通过以下环境变量自定义目录路径：
- `KERAG_HOME`: 自定义全局作用域的根目录。
- `KERAG_LOCAL`: 自定义局部作用域的根目录。

### 作用域切换
在执行模块管理命令（如 `install`, `list`, `scan`, `remove`）时，可以通过参数指定作用域：
- `-g` 或 `--global`: 操作全局作用域。
- `-l` 或 `--local`: 操作局部作用域。

## 📝 最简案例

创建一个名为 `index.md` 的文件：

```markdown
# 线性代数 [@linear-algebra]

线性代数是关于向量空间的数学分支。

## 向量 [@vector]
向量是具有大小和方向的量。

## 参见
(@vector): 向量简介
```

## 📦 模块管理

### 打包模块
要分发您的知识库，请将其打包为 `.tar` 归档文件：

```bash
kerag tool pack ./my-module --name my-module --version 1.0.0 -o my-module.tar
```

### 安装模块
您可以从本地路径、URL 或 Git 仓库安装模块：

```bash
# 从本地 tar 包安装
kerag install ./my-module.tar

# 从远程 tar 包 URL 安装
kerag install https://example.com/module.tar

# 从 GitHub 仓库安装
kerag install git+https://github.com/username/kerag-module.git
```

## 🖥️ 知识库检视与 AI 搜索

KERAG 提供配套项目，用于知识库的可视化检视和 AI 驱动搜索。

| 项目 | 描述 | 链接 |
|---------|-------------|------|
| **KERAG Web** | 可视化知识浏览器（Web 界面） | [TongWang-AI4S/kerag-web](https://github.com/TongWang-AI4S/kerag-web) |
| **KERAG MCP** | AI 助手集成（MCP 服务器） | [TongWang-AI4S/kerag-mcp](https://github.com/TongWang-AI4S/kerag-mcp) |
| **KERAG Modules** | 预构建知识库模块（可直接安装的 tar 文件） | [TongWang-AI4S/KERAG-Modules](https://github.com/TongWang-AI4S/KERAG-Modules) |

### KERAG Web - 可视化知识浏览器
用于浏览和搜索知识库的现代化 Web 界面。

**安装并运行：**
```bash
pip install git+https://github.com/TongWang-AI4S/kerag-web.git
kerag-web
```
访问 http://localhost:8001 即可通过树形导航、全文搜索和富内容展示来浏览您的知识库。

### KERAG MCP - AI 助手集成
MCP (Model Context Protocol) 服务器，使 AI 助手能够访问和导航您的知识库。

**安装：**
```bash
pip install git+https://github.com/TongWang-AI4S/kerag-mcp.git
```

**在 AI 客户端中配置（如 Claude Code）：**
添加到 `.mcp.json`：
```json
{
  "mcpServers": {
    "knowledge-explorer": {
      "type": "stdio",
      "command": "kerag-mcp"
    }
  }
}
```
配置后，AI 助手即可从您的知识库中搜索和检索精确的上下文信息。

### KERAG Modules - 预构建知识库
一系列打包为 `.tar` 归档的即用型知识库模块。无需从源码构建，可直接安装使用。

**安装预构建模块：**
```bash
# 从 GitHub 仓库安装
kerag install https://github.com/TongWang-AI4S/KERAG-Modules/releases/heads/main/module-name.tar
```

浏览 [KERAG-Modules 仓库](https://github.com/TongWang-AI4S/KERAG-Modules) 查找更多可用知识库。

## 📄 开源协议

本项目采用 MIT 开源协议。