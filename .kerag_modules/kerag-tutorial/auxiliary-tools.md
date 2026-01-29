# Auxiliary Tools [@auxiliary-tools]

## Document Splitting Tool [@doc-split]

To quickly convert large Markdown documents into KERAG knowledge structures, we provide the `split` tool. This tool can automatically split long documents by specified heading levels and generate a main index file with subtree references.

### Basic Usage

```bash
# Split document at ### level (default)
kerag tool split my-document.md

# Split at ## level and output to custom directory
kerag tool split my-document.md -l 2 -o my-knowledge-base

# Automatically add [@label] tags to all headings
kerag tool split my-document.md --all-labeled
```

### Parameter Description

- `file`: Markdown file to split (required parameter)
- `-o, --output`: Output directory, defaults to `output`
- `-l, --level`: Split level, defaults to 3 (i.e., ### level)
- `--all-labeled`: Automatically add labels to all headings

### How It Works

1. Identifies target level headings (e.g., ###)
2. Creates independent Markdown files for each target heading
3. Replaces original positions with subtree references `## (@label::label)`
4. Automatically generates main index file (`index.md`)
5. Preserves content within code blocks to avoid misjudgment
6. Automatically adjusts heading levels in sub-files

### Node ID Generation Rules

The tool automatically generates node IDs based on headings according to these rules:
- Convert heading to lowercase
- Replace all special symbols and spaces with hyphens `-`
- Replace multiple consecutive hyphens with a single hyphen
- Remove leading and trailing hyphens
- If result is empty, use `untitled`

Examples:
- `# Linear Algebra` → Node ID: `linear-algebra`
- `# Matrix & Vector Space` → Node ID: `matrix-vector-space`
- `# Hello World!` → Node ID: `hello-world`

### Example

Assume a document `math-overview.md`:
```markdown
# Math Overview

## Linear Algebra
Linear algebra studies vector spaces.

## Calculus
Calculus studies rates of change.

### Derivatives
Derivatives represent instantaneous rates of change.

### Integral
Integrals represent accumulated quantities.
```

After executing `kerag tool split math-overview.md -l 2`, the following will be generated:
```
output/
├── index.md          # Main index, containing ## (@linear-algebra::linear-algebra) etc.
├── linear-algebra.md # Linear algebra content
└── calculus.md       # Calculus content (including Derivatives and Integral subsections)
```

This is a powerful tool for quickly building preliminary knowledge trees, especially suitable for processing existing large documents.

## Module Packaging Tool [@module-pack-tool]

The `pack` tool is used to package knowledge modules into distributable archive files. See (@module-pack::module-pack) section for details.

**Basic Usage**:
```bash
kerag tool pack ./my-module --name my-module --version 1.0.0 -o my-module.tar
```
