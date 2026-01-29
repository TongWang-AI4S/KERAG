# KERAG (Knowledge Explorer Retrieval Augmented Generation)

KERAG is a powerful system designed to transform Markdown files with custom syntax into a hierarchical, cross-referenced knowledge-tree structure for knowledge retrieval and AI-driven exploration.

## 🚀 Installation

You can install the core library directly from GitHub:

```bash
pip install git+https://github.com/TongWang-AI4S/KERAG.git
```

## ✨ Key Features

- **Hierarchical Node Structure**: Transforms linear Markdown into a navigable tree.
- **Custom Syntax**:
    - `[@label]`: Define node anchors.
    - `(@node_id)`: Create cross-references.
    - `## (@referred_node_id)`: Embed subtrees.

## 🌳 Quick Knowledge Tree Building

Use the `kerag tool split` command to quickly build a preliminary knowledge tree from a large Markdown document:

```bash
# Split a document at ### level (default)
kerag tool split my-document.md

# Split at ## level and output to custom directory
kerag tool split my-document.md -l 2 -o my-knowledge-base

# Auto-add labels to all headings
kerag tool split my-document.md --all-labeled
```

This command will:
- Create a main `index.md` file with subtree references
- Generate separate files for each section at the specified heading level
- Automatically adjust heading levels in sub-files

## 📂 Knowledge Base Directories & Scopes

KERAG supports two scopes for knowledge base management, allowing you to flexibly organize general and project-specific knowledge:

- **Global Scope**: Default path is `~/.kerag_modules`. Used for general knowledge modules accessible across all projects.
- **Local Scope**: Default path is `./.kerag_modules` in the current working directory. Used for specialized knowledge modules relevant only to the current project.

### Environment Configuration
You can customize the directory paths using the following environment variables:
- `KERAG_HOME`: Customize the global scope root directory.
- `KERAG_LOCAL`: Customize the local scope root directory.

### Scope Switching
When executing module management commands (e.g., `install`, `list`, `scan`, `remove`), you can specify the scope using these flags:
- `-g` or `--global`: Target the global scope.
- `-l` or `--local`: Target the local scope.

## 📝 Minimal Example

Create a file named `index.md`:

```markdown
# Linear Algebra [@linear-algebra]

Linear algebra is the branch of mathematics concerning vector spaces.

## Vectors [@vector]
Vectors are quantities with both magnitude and direction.

## See Also
(@vector): Introduction to vectors
```

## 📦 Module Management

### Packing a Module
To distribute your knowledge base, pack it into a `.tar` archive:

```bash
kerag tool pack ./my-module --name my-module --version 1.0.0 -o my-module.tar
```

### Installing a Module
You can install modules from local paths, URLs, or Git repositories:

```bash
# Install from a local tarball
kerag install ./my-module.tar

# Install from a remote tarball URL
kerag install https://example.com/module.tar

# Install from a GitHub repository
kerag install git+https://github.com/username/kerag-module.git
```

## 🖥️ Knowledge Base Viewing & AI Search

KERAG provides companion projects for knowledge base exploration and AI-driven search.

| Project | Description | Link |
|---------|-------------|------|
| **KERAG Web** | Visual knowledge explorer with web interface | [TongWang-AI4S/kerag-web](https://github.com/TongWang-AI4S/kerag-web) |
| **KERAG MCP** | MCP server for AI assistant integration | [TongWang-AI4S/kerag-mcp](https://github.com/TongWang-AI4S/kerag-mcp) |
| **KERAG Modules** | Pre-built knowledge base modules (tar archives ready to install) | [TongWang-AI4S/KERAG-Modules](https://github.com/TongWang-AI4S/KERAG-Modules) |

### KERAG Web - Visual Knowledge Explorer
A modern web interface for browsing and searching your knowledge base.

**Install and run:**
```bash
pip install git+https://github.com/TongWang-AI4S/kerag-web.git
kerag-web
```
Visit http://localhost:8001 to browse your knowledge base with tree navigation, full-text search, and rich content display.

### KERAG MCP - AI Assistant Integration
An MCP (Model Context Protocol) server that enables AI assistants to access and navigate your knowledge base.

**Install:**
```bash
pip install git+https://github.com/TongWang-AI4S/kerag-mcp.git
```

**Configure in your AI client (e.g., Claude Code):**
Add to `.mcp.json`:
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

This allows AI assistants to search and retrieve precise context from your knowledge base.

### KERAG Modules - Pre-built Knowledge Bases
A collection of ready-to-use knowledge base modules packaged as `.tar` archives. Install directly without building from source.

**Install a pre-built module:**
```bash
# Install from the GitHub repository
kerag install https://github.com/TongWang-AI4S/KERAG-Modules/releases/heads/main/module-name.tar
```

Browse the [KERAG-Modules repository](https://github.com/TongWang-AI4S/KERAG-Modules) to find available knowledge bases.

## 📄 License

This project is licensed under the MIT License.