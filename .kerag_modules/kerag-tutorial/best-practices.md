# Best Practices Guide [@best-practices]

To help you build KERAG knowledge bases with clear structure, easy navigation, and AI-friendly retrieval, we have compiled the following best practices:

## Module and File Organization [@module-organization]

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

## Headings and Hierarchical Structure [@heading-structure]

### Logical Hierarchy

- **Consistency**: Strictly follow Markdown heading levels (# to ######). Knowledge tree building depends on heading count to determine structure.
- **Depth Control**: If a single file's section hierarchy exceeds 6 levels, it is recommended to use **Subtree References** to split content into independent files to maintain concise literal depth.

### Subtree References

- **Syntax**: `## (@other_file::label)`.
- **Principles**:
    - Avoid subtree references to ancestors (upward) or distant collateral (cross-module).
    - Referenced files should preferably be in current directory or subdirectories.
    - Subtree references are the core means of managing large knowledge trees; treat them as tools for "modularizing" documents.

## Naming and ID System [@naming-id]

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

## Cross-References and Associations [@cross-references]

### Inline Links

- **Scenario**: Use `(@node_id)` when mentioning related concepts in body text.
- **Effect**: The system automatically extracts these links and displays them as "related links" in node views, but does not change the document's tree hierarchy.

### See Also

- **Syntax**: Use special `# See Also` or `# 参见` heading.
- **Format**: Each line below should strictly follow the `(@node_id): description text` format.
- **Purpose**: Used to establish strong associations that do not belong to parent-child relationships.

## Content Writing Suggestions [@content-tips]

### Code Fences

- **Safety**: All content within code fences (including lines with `#`) is forcibly parsed as plain text content and will not trigger section splitting. When writing technical documents containing code examples, please always wrap them with ```.

### Paragraph Separation

- **Note**: In KERAG, empty lines between paragraphs generate multiple `ContentNode`s. If you want a piece of text to be logically unified, please minimize unnecessary empty lines.
