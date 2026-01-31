# KERAG (Knowledge Explorer Retrieval Augmented Generation)

KERAG 是一个将成体系的知识（如笔记、书目、经验总结）进行**结构化组织、打包分发**并提供 **AI 访问接口**的工具。

它与传统 RAG 的区别在于：它不只是将文档切碎，而是将 Markdown 文件解析为具有逻辑层级的“知识树”。这种结构允许 AI Agent 像人类翻阅教科书目录一样，通过层级导航来精准定位和检索知识。

## 核心特性

* **结构化知识树**：将线性的 Markdown 文档转化为可导航的节点树，保留章节间的逻辑层级。
* **扩展 Markdown 语法**：
  * `[@label]`：定义节点锚点标签。
  * `(@node_id)`：创建交叉引用。
  * `## (@referred_node_id)`：通过引用直接嵌入整个子树。
* **知识包管理**：仿照 `pip` 的逻辑，支持知识库的打包 (`pack`)、共享与安装 (`install`)。
* **双重作用域**：支持全局 (Global) 和项目局部 (Local) 知识库管理。
* **使用支持**：提供 Web 检视页面 (KERAG-Web) 和标准 MCP 接口 (KERAG-MCP)。

## 适用范围
KERAG 专为高度结构化、层级化的内容而设计：

**最适合的场景：**
* **技术文档：** 代码文档、API 参考手册。
* **教育材料：** 结构化的教程、教科书、学术笔记。
* **知识库：** 个人经验总结、百科条目。
* **层级文档：** 任何具有清晰章、节、小节结构的内容。

**不适用的场景：**
* **叙事内容：** 小说、散文或故事情节。
* **非结构化文档：** 单篇的新闻报导或随笔博文。
* **流式记录：** 聊天记录、会议对话转录。
* **碎片信息：** 任何缺乏明确层级逻辑的扁平内容。

---

## 安装

你可以直接从 GitHub 安装核心库：

```bash
pip install git+https://github.com/TongWang-AI4S/KERAG.git
```

## 快速构建知识树

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

* 创建带有子树引用的主 `index.md` 文件。
* 为指定标题级别的每个章节生成独立文件。
* 自动调整子文件中的标题层级。

## 知识库目录与作用域

KERAG 允许您灵活组织通用知识和项目特定知识：

* **全局作用域 (Global)**: 默认路径为 `~/.kerag_modules`。存放可供所有项目访问的通用知识模块。
* **局部作用域 (Local)**: 默认路径为当前工作目录下的 `./.kerag_modules`。存放仅与当前项目相关的专业知识模块。

### 环境变量配置

* `KERAG_HOME`: 自定义全局作用域的根目录。
* `KERAG_LOCAL`: 自定义局部作用域的根目录。

### 作用域切换

在执行模块管理命令（如 `install`, `list`, `scan`, `remove`）时，可以通过参数指定作用域：

* `-g` 或 `--global`: 操作全局作用域。
* `-l` 或 `--local`: 操作局部作用域。

## 最简案例

创建一个名为 `index.md` 的文件：

```markdown
# 线性代数 [@linear-algebra]

线性代数是关于向量空间的数学分支。

## 向量 [@vector]
向量是具有大小和方向的量。

## 参见
(@vector): 向量简介

```

## 模块管理

### 打包模块

要分发您的知识库，可以通过`kerag tool pack`工具快速将其打包为 `.tar` 归档文件：

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

## 知识库检视与 AI 搜索

KERAG 提供配套项目，用于知识库的可视化检视和 AI 驱动搜索。

| 项目 | 描述 | 链接 |
| --- | --- | --- |
| **KERAG Web** | 可视化知识浏览器（Web 界面） | [TongWang-AI4S/kerag-web](https://github.com/TongWang-AI4S/kerag-web) |
| **KERAG MCP** | AI 助手集成（MCP 服务器） | [TongWang-AI4S/kerag-mcp](https://github.com/TongWang-AI4S/kerag-mcp) |

### KERAG Web - 可视化知识检视界面

用于检视知识库的本地 Web 界面。

**安装并运行：**

```bash
pip install git+https://github.com/TongWang-AI4S/kerag-web.git
kerag-web
```

访问 http://localhost:8001 即可通过树形导航、全文搜索来浏览您的知识库。

### KERAG MCP - AI 助手集成

MCP (Model Context Protocol) 服务器，使 AI 助手（如 Claude Code, Cursor）能够访问和导航您的知识库。

**安装：**

```bash
pip install git+https://github.com/TongWang-AI4S/kerag-mcp.git
```

**在 AI 客户端中配置（如 Claude Code）：**
添加到配置文件的 `mcpServers` 字段中：

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

> ### KERAG Modules - 知识库分享
> 
> 在[KERAG-Modules](https://github.com/TongWang-AI4S/KERAG-Modules)仓库，本人会分享一些自己生成的知识库模块，可以直接安装到自己的 KERAG 环境中使用。
> 
> ```bash
> kerag install kerag install https://raw.githubusercontent.com/TongWang-AI4S/KERAG-Modules/refs/heads/main/example/module-name.tar
> ```

## 开源协议

本项目采用 MIT 开源协议。
