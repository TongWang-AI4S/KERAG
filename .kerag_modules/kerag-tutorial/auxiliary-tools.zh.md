# 辅助工具 [@auxiliary-tools]

## 文档分割工具 [@doc-split]

为了快速将大型 Markdown 文档转换为 KERAG 知识结构，我们提供了 `split` 工具。这个工具可以自动将长文档按指定标题级别分割成多个文件，并生成带有子树引用的主索引文件。

### 基本用法

```bash
# 在 ### 级别分割文档（默认）
kerag tool split my-document.md

# 在 ## 级别分割并输出到自定义目录
kerag tool split my-document.md -l 2 -o my-knowledge-base

# 自动为所有标题添加 [@label] 标签
kerag tool split my-document.md --all-labeled
```

### 参数说明

- `file`: 要分割的 Markdown 文件（必需参数）
- `-o, --output`: 输出目录，默认为 `output`
- `-l, --level`: 分割层级，默认为 3（即 ### 级别）
- `--all-labeled`: 自动为所有标题添加标签

### 工作原理

1. 识别目标层级的标题（如 ###）
2. 为每个目标标题创建独立的 Markdown 文件
3. 在原位置使用子树引用 `## (@label::label)` 替代
4. 自动生成主索引文件（`index.md`）
5. 保留代码块内的内容，避免误判
6. 自动调整子文件中标题的层级

### 节点ID生成规则

工具会根据标题自动生成节点的ID，规则如下：
- 将标题转换为小写
- 将所有特殊符号和空格替换为连字符 `-`
- 将多于一个的连字符替换为一个连字符
- 移除开头和结尾的连字符
- 如果处理后为空，则使用 `untitled`

例如：
- `# Linear Algebra` → 节点ID: `linear-algebra`
- `# Matrix & Vector Space` → 节点ID: `matrix-vector-space`
- `# Hello World!` → 节点ID: `hello-world`

### 示例

假设有一个文档 `math-overview.md`：
```markdown
# 数学概述

## Linear Algebra
线性代数研究向量空间。

## Calculus
微积分研究变化率。

### Derivatives
导数表示瞬时变化率。

### Integral
积分表示累积量。
```

执行 `kerag tool split math-overview.md -l 2` 后，将生成：
```
output/
├── index.md          # 主索引，包含 ## (@linear-algebra::linear-algebra) 等引用
├── linear-algebra.md # 线性代数内容
└── calculus.md       # 微积分内容（包含导数和积分子章节）
```

这是一个快速构建初步知识树的有力工具，特别适合处理已有的大型文档。

## 模块打包工具 [@module-pack-tool]

`pack` 工具用于将知识模块打包为可分发的归档文件，详见(@module-pack::module-pack)部分。

**基本用法**:
```bash
kerag tool pack ./my-module --name my-module --version 1.0.0 -o my-module.tar
```
