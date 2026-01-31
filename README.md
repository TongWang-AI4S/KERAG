# KERAG (Knowledge Explorer Retrieval Augmented Generation)

KERAG is a tool designed to structurally organize and package systematic knowledge (such as notes, bibliographies, and accumulated experiences) for distribution, while providing a dedicated AI access interface.

When handling domain-specific tasks, an Agent's performance often depends on the background knowledge it can access. If an Agent is provided with a set of highly organized and logically clear reference materials, its effectiveness improves significantly. Much like how we reuse modules from pip or npm, we believe "knowledge" should also be something that can be downloaded, installed, and reused. KERAG aims to achieve this "Knowledge Modularization," turning systematically organized expertise into distributable and assemblable assets, thereby empowering Agents to better tackle tasks across various fields.

Furthermore, for highly structured domain knowledge, we have adopted a style that parses Markdown files into a "Knowledge Tree" with logical hierarchies. This structure allows AI Agents to navigate through levels—much like a human flipping through a textbook's table of contents—to precisely locate and retrieve information. This approach serves as a powerful complement to traditional Vector Retrieval-based RAG.

## Core Features

* **Structured Knowledge Tree**: Transforms linear Markdown documents into a navigable node tree, preserving the logical hierarchy between chapters.
* **Extended Markdown Syntax**:
  * `[@label]`: Defines a node anchor label.
  * `(@node_id)`: Creates a cross-reference.
  * `## (@referred_node_id)`: Directly embeds an entire subtree via reference.
* **Knowledge Package Management**: Follows `pip`-like logic, supporting the `pack`, sharing, and `install` of knowledge bases.
* **Dual Scoping**: Supports both Global and Local (project-specific) knowledge base management.
* **Integration Support**: Provides a web inspector (KERAG-Web) and a standard MCP interface (KERAG-MCP).

## Scope of Application

KERAG is specifically designed for highly structured, hierarchical content:

**Best For:**

* **Technical Documentation:** Code documentation, API reference manuals.
* **Educational Materials:** Structured tutorials, textbooks, academic notes.
* **Knowledge Bases:** Personal experience summaries, encyclopedia entries.
* **Hierarchical Documents:** Any content with a clear structure of parts, chapters, and sections.

**Not Recommended For:**

* **Narrative Content:** Novels, essays, or plot-driven stories.
* **Unstructured Documents:** Single news reports or casual blog posts.
* **Streaming Logs:** Chat history, meeting transcripts.
* **Fragmented Information:** Any flat content lacking clear hierarchical logic.

---

## Installation

You can install the core library directly from GitHub:

```bash
pip install git+https://github.com/TongWang-AI4S/KERAG.git
```

## Quickly Building a Knowledge Tree

Use the `kerag tool split` command to quickly build an initial knowledge tree from a large Markdown document:

```bash
# Split document at the ### level (default)
kerag tool split my-document.md

# Split at the ## level and output to a custom directory
kerag tool split my-document.md -l 2 -o my-knowledge-base

# Automatically add labels to all headers
kerag tool split my-document.md --all-labeled

```

This command will:

* Create a master `index.md` file with subtree references.
* Generate independent files for each section at the specified header level.
* Automatically adjust header hierarchies within sub-files.

## Directories and Scopes

KERAG allows you to flexibly organize general and project-specific knowledge:

* **Global Scope**: Default path is `~/.kerag_modules`. Stores general knowledge modules accessible to all projects.
* **Local Scope**: Default path is `./.kerag_modules` in the current working directory. Stores specialized modules relevant only to the current project.

### Environment Configuration

* `KERAG_HOME`: Customize the root directory for the Global scope.
* `KERAG_LOCAL`: Customize the root directory for the Local scope.

### Scope Switching

When executing management commands (such as `install`, `list`, `scan`, `remove`), you can specify the scope via arguments:

* `-g` or `--global`: Operations on the Global scope.
* `-l` or `--local`: Operations on the Local scope.

## Minimal Example

Create a file named `index.md`:

```markdown
# Linear Algebra [@linear-algebra]

Linear algebra is the branch of mathematics concerning vector spaces.

## Vectors [@vector]
A vector is a quantity having direction as well as magnitude.

## See Also
(@vector): Introduction to Vectors

```

## Module Management

### Packing a Module

To distribute your knowledge base, use the `kerag tool pack` utility to compress it into a `.tar` archive:

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

## Inspection and AI Search

KERAG provides companion projects for visualization and AI-driven search.

| Project | Description | Link |
| --- | --- | --- |
| **KERAG Web** | Visual knowledge browser (Web UI) | [TongWang-AI4S/kerag-web](https://github.com/TongWang-AI4S/kerag-web) |
| **KERAG MCP** | AI Assistant integration (MCP Server) | [TongWang-AI4S/kerag-mcp](https://github.com/TongWang-AI4S/kerag-mcp) |

### KERAG Web - Visual Inspector

A local web interface for inspecting your knowledge base.

**Install and Run:**

```bash
pip install git+https://github.com/TongWang-AI4S/kerag-web.git
kerag-web

```

Access http://localhost:8001 to browse your knowledge base via tree navigation and full-text search.

### KERAG MCP - AI Assistant Integration

An MCP (Model Context Protocol) server that enables AI assistants (e.g., Claude Code, Cursor) to access and navigate your knowledge base.

**Install:**

```bash
pip install git+https://github.com/TongWang-AI4S/kerag-mcp.git

```

**Configuration (e.g., Claude Code):**
Add the following to the `mcpServers` field in your configuration file:

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

> In the repository [KERAG-Modules](https://github.com/TongWang-AI4S/KERAG-Modules), I share knowledge modules I’ve generated. You can install them directly into your KERAG environment.
> ```bash
> kerag install https://raw.githubusercontent.com/TongWang-AI4S/KERAG-Modules/refs/heads/main/example/module-name.tar
> 
> ``` 

## License

This project is licensed under the MIT License.
