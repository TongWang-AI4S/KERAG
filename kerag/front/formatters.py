"""Formatters for converting explorer data into various string representations."""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseFormatter(ABC):
    """Abstract base class for all formatters."""

    @abstractmethod
    def format(self, data: Dict[str, Any], **kwargs) -> str:
        """Format the provided data dictionary into a string."""
        pass

    def __call__(self, data: Dict[str, Any], **kwargs):
        return self.format(data, **kwargs)


class JSONFormatter(BaseFormatter):
    """Formatter that converts data to a JSON string."""

    def __init__(self, indent: int = 4, sort_keys: bool = False):
        self.indent = indent
        self.sort_keys = sort_keys

    def format(self, data: Dict[str, Any], **kwargs) -> str:
        indent = kwargs.get('indent', self.indent)
        sort_keys = kwargs.get('sort_keys', self.sort_keys)
        return json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)


class TreeFormatter(BaseFormatter):
    """Formatter that displays node hierarchy as a tree."""

    def __init__(self, indent_size: int = 2, show_metadata: bool = False):
        self.indent_size = indent_size
        self.show_metadata = show_metadata

    def format(self, data: Dict[str, Any], **kwargs) -> str:
        if "error" in data:
            return f"Error: {data['error'].get('message', 'Unknown error')}"

        show_metadata = kwargs.get('show_metadata', self.show_metadata)

        lines = []
        self._format_node(data, 0, lines, is_last=True, prefix="", show_metadata=show_metadata)
        return "\n".join(lines)

    def _format_node(self, node: Dict[str, Any], depth: int, lines: List[str],
                     is_last: bool, prefix: str, show_metadata: bool = False):
        # Determine markers
        marker = "└── " if is_last else "├── "
        if depth == 0:
            marker = ""
            new_prefix = ""
        else:
            new_prefix = prefix + ("    " if is_last else "│   ")

        # Node display text
        node_type = node.get("type", "unknown")
        icon = "📁" if node_type == "section" else "📄"

        label = node.get("label", "")
        title = node.get("title", "")

        display_name = title if title else label
        line = f"{prefix}{marker}{icon} {display_name}"

        if show_metadata:
            meta = []
            if "node_id" in node: meta.append(f"ID: {node['node_id']}")
            if label and label != title: meta.append(f"[@{label}]")
            if meta:
                line += f" ({', '.join(meta)})"

        lines.append(line)

        # Handle content preview if it's a content node and has it
        if node_type == "content":
            content = node.get("content") or node.get("content_preview")
            if content:
                content_lines = content.strip().split("\n")
                content_prefix = new_prefix + ("    " if depth > 0 else "  ")
                # Show first few lines or truncated
                preview = content_lines[0]
                if len(content_lines) > 1 or len(preview) > 50:
                    preview = preview[:50] + " ... ... "
                lines.append(f"{content_prefix}{preview}")

        # Recurse children
        children = node.get("children", {})
        if children:
            child_items = list(children.values())
            for i, child in enumerate(child_items):
                self._format_node(
                    child,
                    depth + 1,
                    lines,
                    is_last=(i == len(child_items) - 1),
                    prefix=new_prefix,
                    show_metadata=show_metadata
                )


class SearchFormatter(BaseFormatter):
    """Formatter for search results."""

    def format(self, data: Dict[str, Any]) -> str:
        if "error" in data:
            return f"Error: {data['error'].get('message')}"

        results = data.get("results", [])
        if not results:
            return f"No results found for '{data.get('query')}'."

        lines = [f"Search results for '{data.get('query')}' ({len(results)} found):", ""]
        for i, res in enumerate(results, 1):
            line = f"{i:2}. [{res['type'].upper()}] {res['title']} ({res['node_id']})"
            lines.append(line)
            if "excerpt" in res:
                lines.append(f"    ...{res['excerpt']}...")
        return "\n".join(lines)


class ListFormatter(BaseFormatter):
    """Formatter for child node lists with indices."""

    def format(self, data: Dict[str, Any]) -> str:
        if "error" in data:
            return f"Error: {data['error'].get('message')}"

        items = data.get("items", [])
        if not items:
            return "No children found."

        parent_title = data.get("parent_title", data.get("parent_id"))
        lines = [f"Children of {parent_title}:", ""]
        for i, item in enumerate(items, 1):
            line = f"{i:2}. [{item['type'].upper()}] {item['title'] or item['label']}"
            if item.get("has_children"):
                line += " (+)"
            lines.append(line)
        return "\n".join(lines)


class MarkdownFormatter(BaseFormatter):
    """Formatter that reconstructs KERAG Markdown from node dictionaries."""

    def __init__(self, display_mode: str = "full_id", filter_auto_nodes: bool = True, see_also_title: str = "See Also"):
        """
        Args:
            display_mode: 'none' (no labels), 'label' (labels only), 'full_id' (full node IDs)
            filter_auto_nodes: If True, ignore nodes matching __node_X
            see_also_title: Title for the references section (default "See Also")
        """
        self.display_mode = display_mode
        self.filter_auto_nodes = filter_auto_nodes
        self.see_also_title = see_also_title

    def format(self, data: Dict[str, Any], **kwargs) -> str:
        if "error" in data:
            return f"<!-- Error: {data['error'].get('message')} -->"

        display_mode = kwargs.get('display_mode', self.display_mode)
        filter_auto_nodes = kwargs.get('filter_auto_nodes', self.filter_auto_nodes)
        see_also_title = kwargs.get('see_also_title', self.see_also_title)

        lines = []
        # Start rendering from depth 1
        self._render_node(data, lines, current_depth=1, display_mode=display_mode,
                          filter_auto_nodes=filter_auto_nodes, see_also_title=see_also_title)
        return "\n".join(lines).strip() + "\n"

    def _is_auto_node(self, label: str) -> bool:
        import re
        return bool(re.match(r'^__node_\d+$', label))

    def _get_label_suffix(self, node: Dict[str, Any], display_mode: str, filter_auto_nodes: bool) -> str:
        label = node.get("label", "")
        if not label:
            return ""

        if filter_auto_nodes and self._is_auto_node(label):
            return ""

        if display_mode == "full_id":
            return f"[@{node.get('node_id', label)}]"
        elif display_mode == "label":
            # Just the label part, no file prefix
            short_label = label.split("::")[-1] if "::" in label else label
            return f"[@{short_label}]"

        return ""

    def _render_node(self, node: Dict[str, Any], lines: List[str], current_depth: int = 1,
                     display_mode: str = "full_id", filter_auto_nodes: bool = True, see_also_title: str = "See Also"):
        node_type = node.get("type")

        if node_type == "section":
            title = node.get("title", "Untitled")
            suffix = self._get_label_suffix(node, display_mode, filter_auto_nodes)

            lines.append(f"{'#' * current_depth} {title}{suffix}")
            lines.append("")

            # 新增: 如果section有content_preview，显示为引用块
            content_preview = node.get("content_preview")
            if content_preview:
                lines.append("> Preview:")
                lines.append(f"> {content_preview}".replace("\n", "\n> "))
                lines.append("")

            # Recurse children
            children = node.get("children", {})
            for child in children.values():
                self._render_node(child, lines, current_depth + 1, display_mode, filter_auto_nodes, see_also_title)

            # See Also
            see_also = node.get("see_also", [])
            if see_also:
                lines.append(f"{'#' * (current_depth + 1)} {see_also_title}")
                for item in see_also:
                    ref_id = item.get("node_id")
                    desc = item.get("description")
                    line = f"(@{ref_id})"
                    if desc:
                        line += f": {desc}"
                    lines.append(line)
                lines.append("")

        elif node_type == "content":
            suffix = self._get_label_suffix(node, display_mode, filter_auto_nodes)
            content = node.get("content", "")
            if not content and "content_preview" in node:
                content = "> Preview:\n" + f"> {node['content_preview']}".replace("\n", "\n> ")

            if content or suffix:
                text = content
                if suffix:
                    if text:
                        # Append suffix to the last line of content (inline)
                        content_lines = text.rstrip().split("\n")
                        content_lines[-1] = content_lines[-1] + " " + suffix
                        text = "\n".join(content_lines)
                    else:
                        # If no content, just show the label as the node's only representation
                        text = suffix.strip()

                lines.append(text)
                lines.append("")
