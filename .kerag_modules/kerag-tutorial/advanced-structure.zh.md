# 高级结构与多文件系统 [@advanced-structure]

## 案例阶段 3：将单文件拆分为多文件结构 [@case-stage-3]

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

## 跨文件引用与子树嵌入 [@subtree-references]

**子树嵌入 (Subtree References)**:
- **语法**: `# (@external_id)`
- **作用**: 将外部文件（如 `matrix.md`）中的某个章节节点，"挂载"到当前节点下，成为其子树。
- **示例**: `## (@matrix::matrix)` 实际上把 `matrix.md` 的中的matrix节点变成了 `index.md` 中 `# 线性代数` 的子节点。

## 路径简写与 ID 解析 [@path-resolution]

在多文件系统中，节点 ID 格式为 `file_path::label`。KERAG 提供了简写规则：

- **相对路径**: 支持 `./` (同级目录) 和 `../` (上级目录)。
- **根路径**: `/` 开头表示从知识库根目录开始查找。

### Index 文件的特殊处理 [@index-special-handling]

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
