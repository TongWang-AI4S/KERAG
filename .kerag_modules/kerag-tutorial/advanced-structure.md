# Advanced Structure and Multi-File System [@advanced-structure]

## Case Stage 3: Splitting Single File into Multi-File Structure [@case-stage-3]

As the knowledge base grows, single files become difficult to maintain. We need to split them into a folder structure.

> **Tip**: If you already have a long document, you can use the document splitting tool to create an initial structure. See (@auxiliary-tools::doc-split) for details.

## See Also

(@auxiliary-tools::doc-split): Use `kerag tool split` command to quickly split long documents

**New Directory Structure**:
```text
linear-algebra/
├── index.md    (Entry file)
├── matrix.md   (Matrix sub-file)
└── vector.md   (Vector sub-file)
```

**linear-algebra/matrix.md**
```markdown
# Matrices [@matrix]
A matrix is a rectangular array of complex or real numbers.
```

**linear-algebra/vector.md**
```markdown
# Vectors [@vector]
A vector is a quantity that has both magnitude and direction.

## See Also
(@matrix::matrix): Introduction to matrices
<!-- Reference content in index -->
(@index::definition)
```

**linear-algebra/index.md**
```markdown
# Linear Algebra [@linear-algebra]

Linear algebra is a branch of mathematics concerning vector spaces and linear mappings.

<!-- Vector section (Subtree embedding) -->
## (@vector::vector)

<!-- Matrix section (Subtree embedding) -->
## (@matrix::matrix)
```

## Cross-File References and Subtree Embedding [@subtree-references]

**Subtree References**:
- **Syntax**: `# (@external_id)`
- **Purpose**: "Mounts" a section node from an external file (e.g., `matrix.md`) under the current node, making it a subtree.
- **Example**: `## (@matrix::matrix)` effectively turns the matrix node from `matrix.md` into a child node of `# Linear Algebra` in `index.md`.

## Path Abbreviations and ID Resolution [@path-resolution]

In multi-file systems, node ID format is `file_path::label`. KERAG provides shorthand rules:

- **Relative Paths**: Supports `./` (same directory) and `../` (parent directory).
- **Root Path**: Starting with `/` indicates lookup from the knowledge base root directory.

### Special Handling of Index Files [@index-special-handling]

The file ID of **entry files (index.md)** is resolved as the name of their directory:

- File ID of `linear-algebra/index.md` is `linear-algebra` (not `linear-algebra/index`)
- File ID of `linear-algebra/vector/index.md` is `linear-algebra/vector`

This means when referencing nodes in index files, you can directly use the directory path:

```markdown
<!-- Reference the definition node in linear-algebra/index.md -->
(@linear-algebra::definition)

<!-- Instead of (@linear-algebra/index::definition) -->
```

This design makes module entry more concise and aligns with the intuition of treating directories as module wholes.

However, when referencing the index file in the current directory using relative paths, you would write `(@.::definition)` or `(@::definition)`, or explicitly write `(@index::definition)`.
