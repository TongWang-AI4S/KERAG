<!-- Author: Tong Wang -->
<!-- Version: 0.1.0 -->
<!-- Description: KERAG 教程 - 从零构建结构化知识库 -->

# KERAG 教程

本教程将通过一个贯穿始终的案例——**构建线性代数 (Linear Algebra) 知识库**——带领你由浅入深地掌握 KERAG (Knowledge Explorer Retrieval Augmented Generation) 的核心概念与操作流程。

我们将从最简单的单文件开始，逐步添加高级语法，将其拆分为多文件结构，并最终打包成一个可分发的模块。

---

# 核心概念与单文件结构

## 案例阶段 1：创建一个简单的单文件知识库

在 KERAG 中，我们将markdown文本解析为节点与知识树进行检阅。

首先在工作区下，建立一个`./kerag-modules`目录作为KERAG知识文件目录。然后在该目录下创建一个`linear-algebra`目录作为案例模块。

在模块目录下，可以创建名为 `index.md` 的文件，内容如下：

```markdown
# 线性代数

线性代数是关于向量空间和线性映射的数学分支。

## 向量
向量是具有大小和方向的量。

抽象地说，向量是向量空间中的元素。
向量空间是满足特定性质的集合。

## 矩阵
矩阵是一个按照长方阵列排列的复数或实数集合。

<!-- 注释会被节点树构建逻辑直接忽略，目前只支持单行注释 -->
```

## 节点类型

在这个简单的例子中，已经包含了 KERAG 的两种核心节点类型：

**章节节点 (SectionNode)**:
- 由 Markdown 标题 (`#`, `##`, ...) 定义。
- **作用**: 定义知识的层级结构（目录树）。
- **示例**: `# 线性代数` 是根节点，`## 向量` 和 `## 矩阵` 是其子节点。

**内容节点 (ContentNode)**:
- 标题下方的正文文本、列表、代码块等。没有空行分隔的多个行归属于同一个内容节点；空行分隔的两个行属于不同内容节点
- **作用**: 承载具体的知识内容。
- **归属**: 每个内容块都属于它上方最近的一个章节节点。
- **示例**: "向量是具有大小和方向的量。" 是属于 `## 向量` 节点的内容。

## 树状结构可视化

KERAG 会将上述文件解析为如下的逻辑树状结构：

```text
线性代数 (SectionNode)
├── "线性代数是关于..." (ContentNode)
├── 向量 (SectionNode)
│   ├── "向量是具有大小和方向的量。" (ContentNode)
│   └── "抽象地说...\n向量空间是..." (ContentNode)
└── 矩阵 (SectionNode)
    └── "矩阵是一个按照..." (ContentNode)
```

这种结构使得 AI 和人类都能精确地定位和引用知识库中的特定部分，就像从书本的目录进行查找，而不仅仅是搜索整个文件。

---

# 基础语法

## 案例阶段 2：为知识库添加标签和链接

为了让知识点之间建立联系，我们需要使用 KERAG 的扩展语法。现在让我们升级 `linear-algebra/index.md`。

**index.md (v2)**
```markdown
# 线性代数 [@linear-algebra]

线性代数是关于向量空间和线性映射的数学分支。

## 定义 [@definition]
线性代数主要处理向量空间。

## 矩阵 [@matrix]
矩阵可以看作是向量的集合。请参阅 (@vector)。

## 向量 [@vector]
向量是线性代数的基本单元。通常用 (@matrix) 来表示线性变换。

### 参见
(@matrix): 矩阵的介绍
<!-- 对外部模块中节点的参见引用 -->
(@/calculus/multivariate::gradient)
```

## 标签 (Labels)

有的时候我们需要在其它地方引用某些章节或内容，**标签**提供了引用章节的方法。

- **语法**: 在标题行末尾添加 `[@label_name]`。
- **作用**: 指定该节点的唯一标识符后缀。
- **示例**: `## 矩阵 [@matrix]` 的节点 标签即是`matrix`。

## 行内链接 (Inline Links)

在正文中引用其他节点，构建知识网络。

- **语法**: `(@node_id)` 或 `(@label)` (在同一文件中可简写)。
- **示例**: `请参阅 (@vector)` 会创建一个指向向量节点的超链接。

## 参见块 (See Also)

在章节末尾显式列出相关联的知识点，不仅对读者友好，也能增强 RAG 检索的相关性。

- **语法**: 使用 `See Also` 或 `参见` 作为子章节标题。此时该章节将不会被解析为章节节点，而是上级节点的参见块。
- **格式**: 每行一个链接，可选添加描述 `(@node_id): 描述文本`。

---

# 高级结构与多文件系统

## 案例阶段 3：将单文件拆分为多文件结构

随着知识库的增长，单文件变得难以维护。我们需要将其拆分为文件夹结构。

> **提示**：如果已有一个长文档，可以使用文档划分工具划分出初步结构。参见 (@auxiliary-tools::doc-split)。

## 参见

(@auxiliary-tools::doc-split): 使用 `kerag tool split` 命令快速划分长文档

**新目录结构**:
```text
linear-algebra/
├── index.md    (入口文件)
├── matrix.md   (矩阵子文件)
└── vector.md   (向量子文件)
```

**linear-algebra/matrix.md**
```markdown
# 矩阵 [@matrix]
矩阵是一个按照长方阵列排列的复数或实数集合。
```

**linear-algebra/vector.md**
```markdown
# 向量 [@vector]
向量是具有大小和方向的量。

## 参见
(@matrix::matrix): 矩阵的介绍
<!-- 引用index中的内容 -->
(@index::definition)
```

**linear-algebra/index.md**
```markdown
# 线性代数 [@linear-algebra]

线性代数是关于向量空间和线性映射的数学分支。

<!-- 向量部分 (子树嵌入) -->
## (@vector::vector)

<!-- 矩阵部分 (子树嵌入) -->
## (@matrix::matrix)
```

## 跨文件引用与子树嵌入

**子树嵌入 (Subtree References)**:
- **语法**: `# (@external_id)`
- **作用**: 将外部文件（如 `matrix.md`）中的某个章节节点，"挂载"到当前节点下，成为其子树。
- **示例**: `## (@matrix::matrix)` 实际上把 `matrix.md` 的中的matrix节点变成了 `index.md` 中 `# 线性代数` 的子节点。

## 路径简写与 ID 解析

在多文件系统中，节点 ID 格式为 `file_path::label`。KERAG 提供了简写规则：

- **相对路径**: 支持 `./` (同级目录) 和 `../` (上级目录)。
- **根路径**: `/` 开头表示从知识库根目录开始查找。

### Index 文件的特殊处理

**入口文件 (index.md)** 的文件 ID 会被解析为其所在目录的名称：

- `linear-algebra/index.md` 的文件 ID 是 `linear-algebra`（而非 `linear-algebra/index`）
- `linear-algebra/vector/index.md` 的文件 ID 是 `linear-algebra/vector`

这意味着引用 index 文件中的节点时，可以直接使用目录路径：

```markdown
<!-- 引用 linear-algebra/index.md 中的 definition 节点 -->
(@linear-algebra::definition)

<!-- 而非 (@linear-algebra/index::definition) -->
```

这种设计使得模块入口更加简洁，也符合将目录视为模块整体的直觉。

但是，在引用本目录中的index文件时，如果使用相对路径则会写为`(@.::definition)`或`(@::definition)`，此时，也可以显式写作`(@index::definition)`。

---

# 多语言支持

KERAG 支持多语言知识库，允许你为同一内容提供不同语言版本，并根据用户的语言偏好自动选择最合适的版本。

## 文件命名约定

多语言文件通过后缀标识语言版本：

- **默认语言文件**: `filename.md` 或 `index.md`
- **中文版本**: `filename.zh.md` 或 `index.zh.md`
- **英文版本**: `filename.en.md` 或 `index.en.md`
- **其他语言**: 使用 ISO 639-1 两位语言代码（如 `.ja` 日语、`.de` 德语等）

**目录结构示例**:
```text
linear-algebra/
├── index.md           # 默认版本
├── index.zh.md        # 中文版入口
├── index.en.md        # 英文版入口
├── matrix.md          # 默认版本
├── matrix.zh.md       # 中文版矩阵章节
└── matrix.en.md       # 英文版矩阵章节
```

## 语言解析优先级

当系统需要查找某个 `file_id` 对应的物理文件时，会按照以下优先级顺序尝试：

假设当前语言设置为 `zh`，查找 `linear-algebra/matrix`：

1. `linear-algebra/matrix.zh.md` （优先匹配当前语言）
2. `linear-algebra/matrix.md` （回退到默认版本）

对于目录类型的引用（如 `linear-algebra`）：

1. `linear-algebra/index.zh.md` （优先匹配当前语言）
2. `linear-algebra/index.md` （回退到默认版本）

## 文件 ID 与语言无关性

**重要**: 无论使用哪种语言版本，文件 ID 都是相同的。

- `matrix.zh.md` 和 `matrix.en.md` 的文件 ID 都是 `linear-algebra::matrix`
- 引用时无需指定语言：`(@linear-algebra/matrix::content)` 会自动解析为当前语言的版本

这种设计确保了跨语言引用的简洁性和一致性。

## 配置语言偏好

系统通过以下方式确定当前语言：

- **环境变量**: 设置 `KERAG_LANG` 环境变量（如 `zh`, `en`）
- **程序接口**: 在代码中调用时传入 `lang` 参数

```bash
# 设置环境变量后运行命令
export KERAG_LANG=zh
```

## 最佳实践

### 结构一致性
不同语言版本的文件应该保持相同的章节结构和标签命名，确保跨语言引用能够正确解析：

```markdown
<!-- matrix.zh.md -->
# 矩阵 [@matrix]
矩阵是一个按照长方阵列排列的复数或实数集合。

<!-- matrix.en.md -->
# Matrix [@matrix]
A matrix is a rectangular array of complex or real numbers.
```

### 默认语言回退
建议始终提供默认语言版本（不带语言后缀的文件），这样当某个语言版本缺失时，系统可以优雅地回退到默认版本，而不是报错。

---

# 模块管理、打包与安装

## 模块扫描与本地管理 (Scan)

当你在本地创建或修改了模块，运行扫描命令来更新本地注册信息：

```bash
kerag scan
```

此命令会执行以下操作：
1. 遍历局部与全局知识根目录（默认为`workdir/.kerag_modules`与`~/.kerag_modules/`，可以通过环境变量`KERAG_LOCAL`与`KERAG_HOME`指定）寻找包含 `index.md` 的文件夹。
2. 从`index.md`中解析模块元数据。
3. 生成或更新 `.kerag_modules/modules.yml` 索引文件

## 模块打包 (Pack)

为了分发你的知识库，你可以使用打包工具将其转换为标准的 `.tar` 归档文件。

**命令格式**:
```bash
kerag tool pack [模块目录] [-o 输出文件名] [--name 模块名] [--version 版本] [--description 描述]
```

**关键特性**:
- **元数据一致性检查**: 打包工具会严格检查 `index.md`、`--meta` 文件以及命令行参数提供的信息。如果这三者之间存在相互矛盾的定义（如不同的版本号），工具会报错并停止打包。
- **自动生成元数据**: 打包过程会自动在归档文件根目录生成 `kerag_meta.txt`。
- **结构优化**: 打包后的文件结构经过优化，确保解压后能直接被 KERAG 识别和安装。

**案例演示**:
```bash
# 将 linear-algebra 目录打包，显式指定版本和名称
kerag tool pack ./linear-algebra --name linear-algebra-example --version 1.0.0 -o la-v1.tar
```

## 安装外部模块 (Install)

除了在 KERAG 知识路径中自动扫描，你也可以在任何路径下准备好符合规范的模块目录，然后通过 `install` 命令将其安装到 KERAG 系统中。

### 模块目录规范

为了确保 `kerag install` 能正确识别模块，源目录或压缩文件（`.tar`, `.zip`等）必须符合以下结构之一：
1. **单文件夹结构**: 根目录下仅包含一个文件夹，且该文件夹内包含 `index.md`。
2. **显式元数据结构**: 根目录下包含多个文件/文件夹，但必须有一个 `kerag_meta.txt` 文件。该文件的第一行必须指明包含 `index.md` 的实际模块目录名。

**注意**: 使用 `kerag tool pack` 生成的 `.tar` 文件正是严格遵循上述"显式元数据结构"生成的。在进行打包时，应该将目标路径指定为**模块目录本身**（即包含 `index.md` 的那个目录），而不是它的父目录。

### 来源类型

- **Git 仓库**: 使用 `git+` 前缀。
- **远程归档 (HTTP/HTTPS)**: 直接指向归档文件的 URL。支持 `.tar`, `.tar.gz`, `.zip` 格式。
- **本地目录或归档文件**: 本地磁盘路径。

**案例演示 (从远程服务器下载并安装 tar 包)**:
```bash
# 安装一个示例线性代数模块
kerag install https://raw.githubusercontent.com/TongWang-AI4S/KERAG/refs/heads/main/example/linear-algebra-demo-0.0.tar
```

**输出示例**:
```text
Downloading module from https://raw.githubusercontent.com/TongWang-AI4S/KERAG/refs/heads/main/example/linear-algebra-demo-0.0.tar...
Extracting TAR archive...
Successfully installed module: the-first-example
```

**其它安装示例**:
```bash
# 从 Git 仓库安装
kerag install git+https://github.com/username/kerag-physics.git

# 从本地目录安装
kerag install ./my-custom-module-dir

# 强制覆盖已安装的模块 (-f)
kerag install ./module-v2.tar -f
```

---

# 辅助工具

## 文档分割工具

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

## 模块打包工具

`pack` 工具用于将知识模块打包为可分发的归档文件，详见(@module-pack::module-pack)部分。

**基本用法**:
```bash
kerag tool pack ./my-module --name my-module --version 1.0.0 -o my-module.tar
```

---

# 最佳实践指南

为了帮助你构建结构清晰、易于导航且利于 AI 检索的 KERAG 知识库，我们整理了以下最佳实践：

## 模块与文件组织

### 模块命名规范

- **原则**：一个知识库使用一个顶层文件夹（即"模块"）。
- **命名**：使用具有描述性的短横线命名法（kebab-case）。
    - **教材/文献**：包含作者名以区分，如 `linear-algebra-gilbert-strang`。
    - **个人总结**：包含作者或领域，如 `quantum-chemistry-xue-d-e`。
    - **技术文档**：直接使用工具名，如 `openmm-doc`。
- **规模**：单个模块不宜过大，建议按学科或项目边界拆分。

### 入口文件 (index.md)

- **硬性约定**：每个模块根目录必须包含 `index.md`（或 `index.[lang].md`），否则系统无法将其识别为有效模块。
- **根节点**：`index.md` 应当仅包含一个一级标题（Level 1 Header），作为整个模块的根节点（ID 通常映射为 `module_name`）。
- **元数据**：建议在 `index.md` 中使用 HTML 注释存储作者、版本、创建时间等非显示元信息。

### 资源管理

- **图片路径**：推荐将图片统一存放在同级目录的 `img/` 文件夹中。
- **可访问性**：在 Markdown 的 `alt` 字段或标题中详细说明图片内容。这不仅方便人类阅读，更能让读取的纯文本 AI 模型"理解"图片意图。

### 单文件结构规范

- **一级章节限制**：推荐任何一个文件中仅有一个一级章节（即单个 `#` 标题）。
- **标签与文件名一致**：该一级章节的标签应与文件名（除后缀外）相同。例如，文件 `linear-transformations.md` 应包含 `# 线性变换 [@linear-transformations]`。
- **好处**：这种一对一的映射关系使文件结构与节点结构保持一致，便于导航和维护。

## 标题与层级结构

### 逻辑层级

- **一致性**：严格遵守 Markdown 标题层级（# 到 ######）。知识树的构建依赖标题数量来确定结构。
- **深度控制**：如果单个文件的章节层次超过 6 级，建议使用**子树引用 (Subtree Reference)** 将内容拆分到独立文件中，以保持字面深度的简洁。

### 子树引用 (Subtree References)

- **语法**：`## (@other_file::label)`。
- **原则**：
    - 避免向祖先（向上）或旁系（跨模块过远）进行子树引用。
    - 被引用的文件最好位于当前目录或子目录下。
    - 子树引用是管理大型知识树的核心手段，应将其视为"模块化"文档的工具。

## 命名与 ID 系统

### 标签 (Labels) 的使用

- **位置**：标签 `[@label]` 建议在标题行末尾或段落结束后的新行添加。
- **分配原则**：
    - **高频节点**：顶层章节、核心定义、重要定理应添加标签，方便全局引用。
    - **内容节点**：普通段落不需要每个都加标签。仅当该段落需要在其他地方被"参见"或"行内链接"引用时（如：在证明中引用前文的某个特定示例）才添加。

### 引用与寻址 (Path Referencing)

- **相对路径引用**：在引用子目录或同级目录的文件时，**推荐直接以相对路径开始**。在引用当前模块内其他分支内容时，最好用`..`进行相对路径引用。

    *示例*：使用 `(@subfolder/file::label)`，而非`(@module-name/current-folder/subfolder/file::label)` 引用子目录内容。使用`(@../file::label)`而非`(@/module-name/file::label)`引用同模块内容。

- **绝对路径引用**：引用其它模块内容时，**推荐以 `/` 开头**。

    *示例*：使用 `(@/other-module/file::label)` 确保从模块根节点开始定位。

- **短 ID 引用**：在同一个文件内，可以直接使用 `(@label)`，系统会自动补全当前文件的路径。

## 交叉引用与关联

### 行内链接 (Inline Links)

- **场景**：在正文中提到相关概念时，使用 `(@node_id)`。
- **效果**：系统会自动提取这些链接，在节点视图中展示为"相关链接"，但不会改变文档的树状层级。

### 参见 (See Also)

- **语法**：使用特殊的 `# 参见` 或 `# See Also` 标题。
- **格式**：下方每行应为严格的 `(@node_id): 描述文本` 格式。
- **作用**：用于建立强关联但不属于父子关系的逻辑连接。

## 内容编写建议

### 代码围栏 (Code Fences)

- **安全性**：代码围栏内的所有内容（包括带有 `#` 的行）都会被强制解析为纯文本内容，不会触发章节分割。在编写包含代码示例的技术文档时，请务必使用 ``` 包裹。

### 段落分割

- **注意**：在 KERAG 中，段落之间的空行会生成多个 `ContentNode`。如果你希望一段文字在逻辑上是一个整体，请尽量减少不必要的空行。

---

# 结语

通过本教程，你已经掌握了从创建单节点 Markdown 到构建多文件、可分发的 KERAG 模块的全过程。

**核心回顾**:
1. **节点化**: 使用标题定义章节，正文定义内容。
2. **结构化**: 通过嵌入引用 (`# (@id)`) 构建知识树。
3. **标准化**: 使用元数据和 `pack`/`install` 工具进行模块管理。

现在，你可以开始构建属于你自己的知识体系了！
