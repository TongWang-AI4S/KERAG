<!-- Author: Tong Wang -->
<!-- Version: 0.1.0 -->
<!-- Description: KERAG Tutorial - Building Structured Knowledge Base from Scratch -->

# KERAG Tutorial

This tutorial will guide you through the core concepts and workflows of KERAG (Knowledge Explorer Retrieval Augmented Generation) using a consistent case study—**building a Linear Algebra knowledge base**.

We will start from a simple single file, gradually add advanced syntax, split it into a multi-file structure, and finally package it into a distributable module.

---

# Core Concepts and Single File Structure

## Case Stage 1: Creating a Simple Single-File Knowledge Base

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

## Node Types

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

## Tree Structure Visualization

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

---

# Basic Syntax

## Case Stage 2: Adding Labels and Links to the Knowledge Base

To establish connections between knowledge points, we need to use KERAG's extended syntax. Let's upgrade the `linear-algebra/index.md` now.

**index.md (v2)**
```markdown
# Linear Algebra [@linear-algebra]

Linear algebra is a branch of mathematics concerning vector spaces and linear mappings.

## Definitions [@definition]
Linear algebra mainly deals with vector spaces.

## Matrices [@matrix]
Matrices can be seen as collections of vectors. See (@vector).

## Vectors [@vector]
Vectors are the basic units of linear algebra. Usually represented by (@matrix) for linear transformations.

### See Also
(@matrix): Introduction to matrices
<!-- Reference to nodes in external modules -->
(@/calculus/multivariate::gradient)
```

## Labels

Sometimes we need to reference certain sections or content elsewhere. **Labels** provide a way to reference sections.

- **Syntax**: Add `[@label_name]` at the end of the heading line.
- **Purpose**: Specifies the unique identifier suffix for the node.
- **Example**: `## Matrices [@matrix]` has the node label `matrix`.

## Inline Links

Reference other nodes in the body text to build a knowledge network.

- **Syntax**: `(@node_id)` or `(@label)` (can be abbreviated within the same file).
- **Example**: `See (@vector)` creates a hyperlink pointing to the vector node.

## See Also Blocks

Explicitly listing related knowledge points at the end of a section is not only reader-friendly but also enhances RAG retrieval relevance.

- **Syntax**: Use `See Also` or `参见` as a subsection heading. This section will not be parsed as a section node but as the parent node's See Also block.
- **Format**: One link per line, optionally adding a description `(@node_id): description text`.

---

# Advanced Structure and Multi-File System

## Case Stage 3: Splitting Single File into Multi-File Structure

As the knowledge base grows, single files become difficult to maintain. We need to split them into a folder structure.

> **Tip**: If you already have a long document, you can use the document splitting tool to create an initial structure. See Document Splitting Tool section for details.

## See Also

(auxiliary-tools::doc-split): Use `kerag tool split` command to quickly split long documents

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

## Cross-File References and Subtree Embedding

**Subtree References**:
- **Syntax**: `# (@external_id)`
- **Purpose**: "Mounts" a section node from an external file (e.g., `matrix.md`) under the current node, making it a subtree.
- **Example**: `## (@matrix::matrix)` effectively turns the matrix node from `matrix.md` into a child node of `# Linear Algebra` in `index.md`.

## Path Abbreviations and ID Resolution

In multi-file systems, node ID format is `file_path::label`. KERAG provides shorthand rules:

- **Relative Paths**: Supports `./` (same directory) and `../` (parent directory).
- **Root Path**: Starting with `/` indicates lookup from the knowledge base root directory.

### Special Handling of Index Files

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

---

# Multi-Language Support

KERAG supports multi-language knowledge bases, allowing you to provide different language versions for the same content and automatically select the most appropriate version based on user language preferences.

## File Naming Conventions

Multi-language files are identified by suffixes:

- **Default Language Files**: `filename.md` or `index.md`
- **Chinese Version**: `filename.zh.md` or `index.zh.md`
- **English Version**: `filename.en.md` or `index.en.md`
- **Other Languages**: Use ISO 639-1 two-letter language codes (e.g., `.ja` for Japanese, `.de` for German)

**Directory Structure Example**:
```text
linear-algebra/
├── index.md           # Default version
├── index.zh.md        # Chinese entry
├── index.en.md        # English entry
├── matrix.md          # Default version
├── matrix.zh.md       # Chinese matrix section
└── matrix.en.md       # English matrix section
```

## Language Resolution Priority

When the system needs to find the physical file corresponding to a `file_id`, it tries in the following priority order:

Assuming current language is set to `en`, looking up `linear-algebra/matrix`:

1. `linear-algebra/matrix.en.md` (Priority match current language)
2. `linear-algebra/matrix.md` (Fallback to default version)

For directory-type references (e.g., `linear-algebra`):

1. `linear-algebra/index.en.md` (Priority match current language)
2. `linear-algebra/index.md` (Fallback to default version)

## File ID Language Independence

**Important**: Regardless of which language version is used, the file ID remains the same.

- File IDs for both `matrix.zh.md` and `matrix.en.md` are `linear-algebra::matrix`
- No need to specify language when referencing: `(@linear-algebra/matrix::content)` automatically resolves to the current language version

This design ensures cross-language reference simplicity and consistency.

## Configuring Language Preference

The system determines the current language through:

- **Environment Variable**: Set `KERAG_LANG` environment variable (e.g., `zh`, `en`)
- **Program Interface**: Pass `lang` parameter when calling in code

```bash
# Set environment variable before running commands
export KERAG_LANG=en
```

## Best Practices

### Structural Consistency
Different language versions should maintain the same section structure and label naming to ensure cross-language references resolve correctly:

```markdown
<!-- matrix.zh.md -->
# 矩阵 [@matrix]
矩阵是一个按照长方阵列排列的复数或实数集合。

<!-- matrix.en.md -->
# Matrix [@matrix]
A matrix is a rectangular array of complex or real numbers.
```

### Default Language Fallback
It is recommended to always provide a default language version (files without language suffixes), so the system can gracefully fall back to the default version when a specific language version is missing, rather than erroring.

---

# Module Management, Packaging and Installation

## Module Scanning and Local Management (Scan)

When you create or modify modules locally, run the scan command to update local registration information:

```bash
kerag scan
```

This command performs the following operations:
1. Traverses local and global knowledge root directories (defaults to `workdir/.kerag_modules` and `~/.kerag_modules/`, can be specified via `KERAG_LOCAL` and `KERAG_HOME` environment variables) looking for folders containing `index.md`.
2. Parses module metadata from `index.md`.
3. Generates or updates `.kerag_modules/modules.yml` index file.

## Module Packaging (Pack)

To distribute your knowledge base, you can use the packaging tool to convert it into a standard `.tar` archive file.

**Command Format**:
```bash
kerag tool pack [module directory] [-o output filename] [--name module name] [--version version] [--description description]
```

**Key Features**:
- **Metadata Consistency Check**: The packaging tool strictly checks information provided in `index.md`, `--meta` files, and command line arguments. If there are conflicting definitions (e.g., different version numbers), the tool will error and stop packaging.
- **Automatic Metadata Generation**: The packaging process automatically generates `kerag_meta.txt` in the archive root directory.
- **Structure Optimization**: The packaged file structure is optimized to ensure it can be directly recognized and installed by KERAG after extraction.

**Case Demonstration**:
```bash
# Package the linear-algebra directory, explicitly specifying version and name
kerag tool pack ./linear-algebra --name linear-algebra-example --version 1.0.0 -o la-v1.tar
```

## Installing External Modules (Install)

Besides automatic scanning in KERAG knowledge paths, you can also prepare module directories conforming to specifications in any location and install them into the KERAG system via the `install` command.

### Module Directory Specifications

To ensure `kerag install` can correctly identify modules, source directories or archive files (`.tar`, `.zip`, etc.) must conform to one of the following structures:
1. **Single Folder Structure**: Root directory contains only one folder, and that folder contains `index.md`.
2. **Explicit Metadata Structure**: Root directory contains multiple files/folders, but must have a `kerag_meta.txt` file. The first line of this file must specify the actual module directory name containing `index.md`.

**Note**: `.tar` files generated by `kerag tool pack` strictly follow the "Explicit Metadata Structure" mentioned above. When packaging, the target path should be specified as the **module directory itself** (the directory containing `index.md`), not its parent directory.

### Source Types

- **Git Repository**: Use `git+` prefix.
- **Remote Archive (HTTP/HTTPS)**: Direct URL pointing to the archive file. Supports `.tar`, `.tar.gz`, `.zip` formats.
- **Local Directory or Archive File**: Local disk path.

**Case Demonstration (Download and install tar package from remote server)**:
```bash
# Install a sample linear algebra module
kerag install https://raw.githubusercontent.com/TongWang-AI4S/KERAG/refs/heads/main/example/linear-algebra-demo-0.0.tar
```

**Output Example**:
```text
Downloading module from https://raw.githubusercontent.com/TongWang-AI4S/KERAG/refs/heads/main/example/linear-algebra-demo-0.0.tar...
Extracting TAR archive...
Successfully installed module: the-first-example
```

**Other Installation Examples**:
```bash
# Install from Git repository
kerag install git+https://github.com/username/kerag-physics.git

# Install from local directory
kerag install ./my-custom-module-dir

# Force overwrite installed module (-f)
kerag install ./module-v2.tar -f
```

---

# Auxiliary Tools

## Document Splitting Tool

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

## Module Packaging Tool

The `pack` tool is used to package knowledge modules into distributable archive files. See Module Packaging section for details.

**Basic Usage**:
```bash
kerag tool pack ./my-module --name my-module --version 1.0.0 -o my-module.tar
```

---

# Best Practices Guide

To help you build KERAG knowledge bases with clear structure, easy navigation, and AI-friendly retrieval, we have compiled the following best practices:

## Module and File Organization

### Module Naming Conventions

- **Principle**: Use one top-level folder per knowledge base (i.e., "module").
- **Naming**: Use descriptive kebab-case.
    - **Textbooks/Literature**: Include author name to distinguish, e.g., `linear-algebra-gilbert-strang`.
    - **Personal Notes**: Include author or field, e.g., `quantum-chemistry-xue-d-e`.
    - **Technical Documentation**: Use tool name directly, e.g., `openmm-doc`.
- **Scale**: Individual modules should not be too large; splitting by subject or project boundaries is recommended.

### Entry File (index.md)

- **Hard Requirement**: Each module root directory must contain `index.md` (or `index.[lang].md`), otherwise the system cannot recognize it as a valid module.
- **Root Node**: `index.md` should contain only one level 1 heading (Level 1 Header) as the root node of the entire module (ID usually maps to `module_name`).
- **Metadata**: It is recommended to use HTML comments in `index.md` to store non-display metadata such as author, version, creation time.

### Resource Management

- **Image Paths**: Recommended to store images uniformly in an `img/` folder in the same directory.
- **Accessibility**: Describe image content in detail in Markdown's `alt` field or caption. This not only facilitates human reading but also allows pure-text AI models to "understand" image intent.

### Single File Structure Conventions

- **Level 1 Section Limit**: It is recommended that any single file contains only one level 1 section (i.e., single `#` heading).
- **Label Matches Filename**: The level 1 section's label should match the filename (excluding extension). For example, file `linear-transformations.md` should contain `# Linear Transformations [@linear-transformations]`.
- **Benefit**: This one-to-one mapping keeps file structure consistent with node structure, facilitating navigation and maintenance.

## Headings and Hierarchical Structure

### Logical Hierarchy

- **Consistency**: Strictly follow Markdown heading levels (# to ######). Knowledge tree building depends on heading count to determine structure.
- **Depth Control**: If a single file's section hierarchy exceeds 6 levels, it is recommended to use **Subtree References** to split content into independent files to maintain concise literal depth.

### Subtree References

- **Syntax**: `## (@other_file::label)`.
- **Principles**:
    - Avoid subtree references to ancestors (upward) or distant collateral (cross-module).
    - Referenced files should preferably be in current directory or subdirectories.
    - Subtree references are the core means of managing large knowledge trees; treat them as tools for "modularizing" documents.

## Naming and ID System

### Label Usage

- **Position**: Labels `[@label]` are recommended to be added at the end of heading lines or on new lines after paragraph endings.
- **Allocation Principles**:
    - **High-frequency Nodes**: Top-level sections, core definitions, and important theorems should have labels for easy global referencing.
    - **Content Nodes**: Regular paragraphs don't need labels for each. Only add when the paragraph needs to be referenced elsewhere (e.g., referencing a specific earlier example in a proof).

### References and Addressing

- **Relative Path References**: When referencing subdirectories or same-level files, **it is recommended to start directly with relative paths**. When referencing other branches within the same module, preferably use `..` for relative references.

    *Example*: Use `(@subfolder/file::label)` instead of `(@module-name/current-folder/subfolder/file::label)` for subdirectory content. Use `(@../file::label)` instead of `(@/module-name/file::label)` for same-module content.

- **Absolute Path References**: When referencing content from other modules, **it is recommended to start with `/`**.

    *Example*: Use `(@/other-module/file::label)` to ensure positioning from the module root node.

- **Short ID References**: Within the same file, you can directly use `(@label)` and the system will automatically complete the current file's path.

## Cross-References and Associations

### Inline Links

- **Scenario**: Use `(@node_id)` when mentioning related concepts in body text.
- **Effect**: The system automatically extracts these links and displays them as "related links" in node views, but does not change the document's tree hierarchy.

### See Also

- **Syntax**: Use special `# See Also` or `# 参见` heading.
- **Format**: Each line below should strictly follow the `(@node_id): description text` format.
- **Purpose**: Used to establish strong associations that do not belong to parent-child relationships.

## Content Writing Suggestions

### Code Fences

- **Safety**: All content within code fences (including lines with `#`) is forcibly parsed as plain text content and will not trigger section splitting. When writing technical documents containing code examples, please always wrap them with ```.

### Paragraph Separation

- **Note**: In KERAG, empty lines between paragraphs generate multiple `ContentNode`s. If you want a piece of text to be logically unified, please minimize unnecessary empty lines.

---

# Conclusion

Through this tutorial, you have mastered the entire process of building a multi-file, distributable KERAG module from creating single-node Markdown.

**Core Takeaways**:
1. **Node-based**: Use headings to define sections and body text to define content.
2. **Structured**: Build knowledge trees through embedded references (`# (@id)`).
3. **Standardized**: Use metadata and `pack`/`install` tools for module management.

Now, you can start building your own knowledge system!
