# Core Concepts and Single File Structure [@core-concepts]

## Case Stage 1: Creating a Simple Single-File Knowledge Base [@case-stage-1]

In KERAG, we parse Markdown text into nodes and knowledge trees for review.

First, create a `./kerag-modules` directory in your workspace as the KERAG knowledge file directory. Then create a `linear-algebra` directory within it as the case study module.

In the module directory, you can create a file named `index.md` with the following content:

```markdown
# Linear Algebra

Linear algebra is a branch of mathematics concerning vector spaces and linear mappings.

## Vectors
A vector is a quantity that has both magnitude and direction.

Abstractly speaking, vectors are elements of vector spaces.
Vector spaces are sets that satisfy specific properties.

## Matrices
A matrix is a rectangular array of complex or real numbers.

<!-- Comments are directly ignored by the node tree building logic, currently only single-line comments are supported -->
```

## Node Types [@node-types]

This simple example already contains the two core node types of KERAG:

**SectionNode**:
- Defined by Markdown headings (`#`, `##`, ...).
- **Purpose**: Defines the hierarchical structure of knowledge (table of contents tree).
- **Example**: `# Linear Algebra` is the root node, `## Vectors` and `## Matrices` are its child nodes.

**ContentNode**:
- Body text, lists, code blocks, etc. below headings. Multiple lines without empty lines belong to the same content node; lines separated by empty lines belong to different content nodes.
- **Purpose**: Carries specific knowledge content.
- **Belonging**: Each content block belongs to the most recent section node above it.
- **Example**: "A vector is a quantity that has both magnitude and direction." is content belonging to the `## Vectors` node.

## Tree Structure Visualization [@tree-visualization]

KERAG will parse the above file into the following logical tree structure:

```text
Linear Algebra (SectionNode)
├── "Linear algebra is a branch of..." (ContentNode)
├── Vectors (SectionNode)
│   ├── "A vector is a quantity..." (ContentNode)
│   └── "Abstractly speaking...\nVector spaces are..." (ContentNode)
└── Matrices (SectionNode)
    └── "A matrix is a rectangular..." (ContentNode)
```

This structure allows both AI and humans to precisely locate and reference specific parts of the knowledge base, just like looking up from a book's table of contents, rather than just searching the entire file.
