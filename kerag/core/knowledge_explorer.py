"""Knowledge Explorer for navigating and browsing the knowledge graph."""

import fnmatch
import warnings
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from collections import OrderedDict
from datetime import datetime

from .knowledge_manager import KnowledgeManager
from .search_nodes import NodeSearcher


@dataclass
class ExplorerOptions:
    """Configuration options for Knowledge Explorer."""
    include_content: bool = True
    include_see_also: bool = True
    max_depth: int = 3
    content_preview_length: int = 100
    language: str = "zh"
    exclude_modules: List[str] = field(default_factory=list)
    cache_size: int = 100
    verbose: bool = False


class KnowledgeExplorer:
    """Explorer for navigating the knowledge graph with file-system-like interface."""

    def __init__(self, knowledge_manager: KnowledgeManager, options: Optional[ExplorerOptions] = None):
        self.km = knowledge_manager
        self.options = options or ExplorerOptions()
        self.searcher = NodeSearcher(self.km)

        # Navigation state
        self.current_node_id: str = "::ROOT"
        self.history: List[str] = ["::ROOT"]
        self.history_cursor: int = 0

        # Caches
        self._node_cache: OrderedDict[str, Dict] = OrderedDict()
        self._breadcrumb_cache: Dict[str, List[Dict]] = {}

        # Statistics
        self._access_count: Dict[str, int] = {}

    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.options.verbose:
            print(f"[KnowledgeExplorer] {message}")

    def _expand_node_id(self, node_id: Optional[str]) -> str:
        """Expand shorthand node ID using current context."""
        if node_id is None:
            return self.current_node_id

        # Get current file context
        current_file = self.current_node_id.split("::")[0] if "::" in self.current_node_id else ""

        # Use ID manager for normal expansion
        expanded = self.km.id_manager.expand_node_id(node_id, current_file)
        # self._log(f"Expanded node ID: {node_id} -> {expanded} (context: {current_file})")
        return expanded

    def _get_node_title(self, node_id: str) -> str:
        """Get the title of a node, with caching."""
        if node_id in self._node_cache:
            cached = self._node_cache[node_id]
            if cached["type"] == "section":
                return cached["title"]
            else:
                return cached["content"][:50] + " ... ... " if len(cached["content"]) > 50 else cached["content"]

        node = self.km.get_node(node_id)
        if not node:
            return node_id

        if node["node_type"] == "section":
            return node["title"]
        else:
            return node["content"][:50] + " ... ... " if len(node["content"]) > 50 else node["content"]

    def _make_node_dict(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a node data dictionary to explorer internal format."""
        node_type = node["node_type"]
        base_dict = {
            "type": "section" if node_type == "section" else "content",
            "id": node["node_id"],
            "node_id": node["node_id"],
            "parent_id": node["parent_id"],
            "file_id": node["file_id"],
            "module": node["module"],
            "path": node["original_file_path"],
            "line_number": node["line_number"],
            "metadata": {
                "last_accessed": datetime.now().isoformat()
            }
        }

        if node_type == "section":
            base_dict.update({
                "title": node["title"],
                "label": node["label"],
                "literal_level": self._get_section_level(node),
                "children_ids": node.get("children_ids", []),
                "has_children": len(node.get("children_ids", [])) > 0,
                "children": {},  # Will be populated if needed
                "see_also": []
            })

            # Process see_also references
            if self.options.include_see_also and node.get("see_also_id_descs"):
                for ref_id, desc in node["see_also_id_descs"]:
                    base_dict["see_also"].append({
                        "node_id": ref_id,
                        "description": desc,
                        "title": self._get_node_title(ref_id)
                    })

            # Add metadata
            base_dict["metadata"].update({
                "child_count": len(node["children_ids"]),
                "has_see_also": bool(node.get("see_also_id_descs")),
                "see_also_count": len(node.get("see_also_id_descs", []))
            })

        elif node_type == "content":
            base_dict.update({
                "content": node["content"],
                "label": node["label"],
                "level": self._get_content_level(node),
                "inline_links": []
            })

            # Process inline links
            if node.get("inline_links"):
                for link_id in node["inline_links"]:
                    base_dict["inline_links"].append({
                        "link_text": f"(@{link_id})",
                        "target_id": link_id,
                        "target_title": self._get_node_title(link_id),
                        "valid": self.km.get_node(link_id) is not None
                    })

            # Add metadata
            base_dict["metadata"].update({
                "content_length": len(node["content"]),
                "link_count": len(node.get("inline_links", []))
            })

        return base_dict

    def _get_section_level(self, section: Dict[str, Any]) -> int:
        """Determine the hierarchical level of a section."""
        # Count ancestors to determine level
        level = 1
        current_id = section["node_id"]
        while current_id and current_id != "::ROOT":
            node = self.km.get_node(current_id)
            if node and node["parent_id"]:
                parent = self.km.get_node(node["parent_id"])
                if parent and parent["node_type"] == "section":
                    level += 1
                    current_id = node["parent_id"]
                else:
                    break
            else:
                break
        return level

    def _get_content_level(self, content: Dict[str, Any]) -> int:
        """Determine the hierarchical level of a content node (based on parent)."""
        if content["parent_id"]:
            parent = self.km.get_node(content["parent_id"])
            if parent and parent["node_type"] == "section":
                return self._get_section_level(parent)
        return 1

    def _update_cache(self, node_id: str, node_dict: Dict) -> None:
        """Update node cache with LRU eviction."""
        if node_id in self._node_cache:
            # Move to end (most recently used)
            self._node_cache.move_to_end(node_id)
        else:
            # Add new entry
            self._node_cache[node_id] = node_dict

            # Evict oldest if cache is full
            if len(self._node_cache) > self.options.cache_size:
                self._node_cache.popitem(last=False)

    def _get_cached_or_build(self, node_id: str) -> Optional[Dict]:
        """Get node from cache or build it."""
        if node_id in self._node_cache:
            self._access_count[node_id] = self._access_count.get(node_id, 0) + 1
            return self._node_cache[node_id]

        node = self.km.get_node(node_id)
        if node is None:
            return None

        node_dict = self._make_node_dict(node)
        self._update_cache(node_id, node_dict)
        self._access_count[node_id] = self._access_count.get(node_id, 0) + 1
        return node_dict

    def get_node_view(self, node_id: Optional[str] = None, depth: int = 1, include_content: bool = True) -> Dict[str, Any]:
        """Get detailed view of a node with optional children.

        Args:
            node_id: Target node ID (None for current node)
            depth: How many levels of children to include (0 = node only)
            include_content: Whether to include content nodes in results

        Returns:
            Dictionary containing node data and requested children
        """
        target_id = self._expand_node_id(node_id)

        # Get the base node
        cached_node = self._get_cached_or_build(target_id)
        if cached_node is None:
            return {
                "error": {
                    "type": "node_not_found",
                    "message": f"Node '{node_id}' not found under node '{self.current_node_id}'",
                    "node_id": node_id
                }
            }

        # Create a copy to avoid cache pollution when adding children
        node_dict = cached_node.copy()

        # If depth == 0 and it's a section, add content_preview (preview mode)
        if depth == 0 and node_dict["type"] == "section":
            node_dict["content_preview"] = self._get_section_content_preview(node_dict)

        # If depth > 0 and it's a section, get children
        if depth > 0 and node_dict["type"] == "section":
            actual_node = self.km.get_node(target_id)
            if actual_node and actual_node["node_type"] == "section":
                # Get children up to specified depth
                children = self._get_children_recursive(
                    actual_node,
                    depth - 1,
                    include_content,
                    current_depth=0
                )
                node_dict["children"] = children

        return node_dict

    def _get_children_recursive(self, section: Dict[str, Any], remaining_depth: int,
                               include_content: bool, current_depth: int) -> Dict[str, Dict]:
        """Recursively get children of a section node."""
        children = {}

        for child_id in section["children_ids"]:
            cached_child = self._get_cached_or_build(child_id)
            if cached_child is None:
                continue

            # Skip content nodes if not included
            if not include_content and cached_child["type"] == "content":
                continue

            # Create a copy
            child_dict = cached_child.copy()

            # Add to children dict using label as key
            child_label = child_dict.get("label", child_dict["node_id"].split("::")[-1])

            # If we've reached max depth but there are still children, provide a preview
            if remaining_depth == 0:
                preview_dict = {
                    "type": child_dict["type"],
                    "node_id": child_dict["node_id"],
                    "label": child_dict.get("label"),
                    "metadata": child_dict.get("metadata", {})
                }
                if child_dict["type"] == "section":
                    preview_dict["title"] = child_dict.get("title", "")
                    # 新增: 为section节点获取第一个content子节点的预览
                    preview_dict["content_preview"] = self._get_section_content_preview(child_dict)
                else:
                    content = child_dict.get("content", "")
                    limit = self.options.content_preview_length
                    if len(content) > limit:
                        preview_dict["content_preview"] = content[:limit-8] + " ... ... " + content[-5:]
                    else:
                        preview_dict["content_preview"] = content

                children[child_label] = preview_dict
                continue

            children[child_label] = child_dict

            # Recurse for section nodes if depth remains
            if remaining_depth > 0 and child_dict["type"] == "section":
                child_node = self.km.get_node(child_id)
                if child_node and child_node["node_type"] == "section":
                    grand_children = self._get_children_recursive(
                        child_node,
                        remaining_depth - 1,
                        include_content,
                        current_depth + 1
                    )
                    if grand_children:
                        child_dict["children"] = grand_children

        return children

    def get_children(self, node_id: Optional[str] = None) -> List[str]:
        """Get list of children node IDs.

        Args:
            node_id: Parent node ID (None for current node)

        Returns:
            List of child node ID strings
        """
        if node_id:
            resolved = self._resolve_target_id(node_id)
            if "id" in resolved:
                target_id = resolved["id"]
            else:
                return []
        else:
            target_id = self.current_node_id

        node = self.km.get_node(target_id)
        if not node or node["node_type"] != "section":
            return []

        return node.get("children_ids", [])

    def preview_children(self, node_id: Optional[str] = None, node_type: str = "all",
                         sort_by: str = "order") -> Dict[str, Any]:
        """List children of a node with preview information.

        Args:
            node_id: Parent node ID, index, or prefix (None for current node)
            node_type: Filter type "all" | "section" | "content"
            sort_by: Sort order "order"(file order) | "title" | "label"

        Returns:
            Dictionary containing children list and metadata
        """
        if node_id:
            resolved = self._resolve_target_id(node_id)
            if "error" in resolved:
                return {"error": {"type": "resolution_failed", "message": resolved["error"]}}
            if resolved.get("type") == "ambiguous":
                return {
                    "type": "ambiguous_target",
                    "query": node_id,
                    "candidates": resolved["candidates"]
                }
            target_id = resolved["id"]
        else:
            target_id = self.current_node_id

        # Get the parent node
        parent_dict = self._get_cached_or_build(target_id)
        if parent_dict is None:
            return {
                "error": {
                    "type": "node_not_found",
                    "message": f"Node '{node_id}' not found under node '{self.current_node_id}'",
                    "node_id": node_id
                }
            }

        # Only section nodes can have children
        if parent_dict["type"] != "section":
            return {
                "type": "children_list",
                "parent_id": target_id,
                "parent_type": "content",
                "items": [],
                "metadata": {
                    "total_count": 0,
                    "filtered_count": 0,
                    "node_type_filter": node_type
                }
            }

        # Get actual section node data
        section = self.km.get_node(target_id)
        if not section or section["node_type"] != "section":
            return {
                "error": {
                    "type": "invalid_node_type",
                    "message": f"Node '{target_id}' is not a section"
                }
            }

        # Build children list
        items = []
        for child_id in section["children_ids"]:
            child_dict = self._get_cached_or_build(child_id)
            if child_dict is None:
                continue

            # Apply type filter
            if node_type != "all":
                if node_type == "section" and child_dict["type"] != "section":
                    continue
                if node_type == "content" and child_dict["type"] != "content":
                    continue

            # Build list item
            item = {
                "node_id": child_dict["node_id"],
                "label": child_dict.get("label", child_dict["node_id"].split("::")[-1]),
                "type": child_dict["type"],
                "title": child_dict.get("title", ""),
                "file_id": child_dict["file_id"],
                "line_number": child_dict["line_number"]
            }

            # Add type-specific fields
            if child_dict["type"] == "section":
                item["literal_level"] = child_dict["literal_level"]
                item["children_ids"] = child_dict.get("children_ids", [])
                item["has_children"] = child_dict.get("has_children", False)
                # 新增: 为section节点获取第一个content子节点的预览
                item["content_preview"] = self._get_section_content_preview(child_dict)
            else:
                limit = self.options.content_preview_length
                content = child_dict["content"]
                if len(content) > limit:
                    item["content_preview"] = content[:limit-8] + " ... ... " + content[-5:]
                else:
                    item["content_preview"] = content

            items.append(item)

        # Sort items
        if sort_by == "title":
            items.sort(key=lambda x: x.get("title", x["label"]))
        elif sort_by == "label":
            items.sort(key=lambda x: x["label"])
        # "order" means keep original file order

        return {
            "type": "children_list",
            "parent_id": target_id,
            "parent_title": parent_dict.get("title", ""),
            "items": items,
            "metadata": {
                "total_count": len(section["children_ids"]),
                "filtered_count": len(items),
                "node_type_filter": node_type,
                "sort_by": sort_by
            }
        }

    def _get_section_content_preview(self, section_dict: Dict[str, Any]) -> str:
        """获取section节点的内容预览。

        如果section的第一个孩子是content节点，则返回该content的内容预览。
        否则返回空字符串。

        Args:
            section_dict: section节点的字典数据

        Returns:
            内容预览字符串或空字符串
        """
        children_ids = section_dict.get("children_ids", [])
        if not children_ids:
            return ""

        # 获取第一个孩子
        first_child = self._get_cached_or_build(children_ids[0])
        if first_child and first_child["type"] == "content":
            content = first_child["content"]
            limit = self.options.content_preview_length
            if len(content) > limit:
                return content[:limit-8] + " ... ... " + content[-5:]
            return content

        return ""

    def _resolve_target_id(self, target: str) -> Dict[str, Any]:
        """Resolve a target string to a node ID.

        Supports:
        1. Full Node ID (contains ::) - return as is after expansion
        2. Child Index (e.g. "1", "2")
        3. Local file labels and module/file shorthand

        Returns:
            Dict with 'id' (full node id), 'node_id' (alias), or 'candidates' (if ambiguous) or 'error'.
        """
        try:
            # 0. If it looks like a full ID, expand and return immediately
            if "::" in target:
                expanded = self._expand_node_id(target)
                return {"id": expanded, "node_id": expanded}

            # 1. Try treating as child index
            if target.isdigit():
                children_res = self.preview_children()
                idx = int(target) - 1 # 1-based to 0-based
                if 0 <= idx < len(children_res.get("items", [])):
                    res_id = children_res["items"][idx]["node_id"]
                    return {"id": res_id, "node_id": res_id}

            # 2. Try prefix match in children (preserving common UX)
            candidates = []
            children_res = self.preview_children()
            query = target.lower()
            for item in children_res.get("items", []):
                if item["label"].lower().startswith(query) or \
                   item.get("title", "").lower().startswith(query):
                    candidates.append(item)

            if len(candidates) == 1:
                res_id = candidates[0]["node_id"]
                return {"id": res_id, "node_id": res_id}
            elif len(candidates) > 1:
                return {
                    "type": "ambiguous",
                    "query": target,
                    "candidates": candidates
                }

            # 3. Task 16a special rule: Check if it's a label in the current file
            current_file = self.current_node_id.split("::")[0] if "::" in self.current_node_id else ""
            local_node_id = f"{current_file}::{target}"
            if self.km.get_node(local_node_id):
                return {"id": local_node_id, "node_id": local_node_id}

            # 4. Task 16a special rule: Shorthand expansion for path/to/topic -> path/to/topic::topic
            # (Already checked for :: at step 0)
            last_part = target.split('/')[-1]
            target_shorthand = f"{target}::{last_part}"
            # Use standard expansion on this shorthand
            expanded_id = self._expand_node_id(target_shorthand)
            # Check if this node exists
            if self.km.get_node(expanded_id):
                return {"id": expanded_id, "node_id": expanded_id}

            # 5. Fallback to standard ID expansion
            expanded_id = self._expand_node_id(target)
            return {"id": expanded_id, "node_id": expanded_id}

        except Exception as e:
            return {"error": str(e)}

    def navigate_to(self, node_id: str) -> Dict[str, Any]:
        """Navigate to a specific node, updating current position and history.

        Args:
            node_id: Target node ID, index, or prefix

        Returns:
            Dictionary containing the target node view and navigation status.
            If ambiguous, returns list of candidates.
        """
        # self._log(f"Navigating to: {node_id}")
        try:
            resolved = self._resolve_target_id(node_id)

            if "error" in resolved:
                raise Exception(resolved["error"])

            if resolved.get("type") == "ambiguous":
                return {
                    "type": "ambiguous_navigation",
                    "query": node_id,
                    "candidates": resolved["candidates"]
                }

            target_id = resolved["id"]

            # If already at the target node, return special response
            if target_id == self.current_node_id:
                return {
                    "type": "already_at_target",
                    "success": True,
                    "node_id": target_id,
                    "message": "Already at the requested node"
                }

            # Get target node
            target_dict = self._get_cached_or_build(target_id)
            if target_dict is None:
                return {
                    "error": {
                        "type": "node_not_found",
                        "message": f"Node '{node_id}' not found under node '{self.current_node_id}'",
                        "node_id": node_id
                    }
                }

            # Update current position
            self.current_node_id = target_id

            # Update history (clear forward history)
            self.history = self.history[:self.history_cursor + 1]
            self.history.append(target_id)
            self.history_cursor += 1

            # Limit history size
            if len(self.history) > 100:
                self.history.pop(0)
                self.history_cursor -= 1

            # Return the node view
            return {
                "type": "navigation_result",
                "success": True,
                "from_node": self.history[-2] if len(self.history) > 1 else None,
                "to_node": target_id,
                "history_position": self.history_cursor,
                "history_size": len(self.history),
                "node": target_dict
            }

        except Exception as e:
            return {
                "error": {
                    "type": "navigation_failed",
                    "message": f"Failed to navigate to '{node_id}': {str(e)}"
                }
            }

    def navigate_up(self) -> Dict[str, Any]:
        """Navigate to the parent node.

        Returns:
            Dictionary containing navigation result
        """
        current_dict = self._get_cached_or_build(self.current_node_id)
        if current_dict is None:
            return {
                "error": {
                    "type": "current_node_invalid",
                    "message": "Current node is invalid"
                }
            }

        parent_id = current_dict.get("parent_id")
        if not parent_id:
            return {
                "error": {
                    "type": "no_parent",
                    "message": "Current node has no parent",
                    "current_node": self.current_node_id
                }
            }

        return self.navigate_to(parent_id)

    def get_breadcrumb(self, node_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get breadcrumb navigation path for a node.

        Args:
            node_id: Target node ID (None for current node)

        Returns:
            List of breadcrumb items from root to target
        """
        target_id = self._expand_node_id(node_id)

        # Check cache
        if target_id in self._breadcrumb_cache:
            return self._breadcrumb_cache[target_id]

        # Build breadcrumb by traversing up the hierarchy
        breadcrumb = []
        current = target_id

        # Loop until we hit the global root or have no more parents
        while current and current != "::ROOT":
            node_dict = self._get_cached_or_build(current)
            if node_dict is None:
                break

            breadcrumb_item = {
                "id": current,
                "label": node_dict.get("label", current.split("::")[-1]),
                "type": node_dict["type"],
                "title": node_dict.get("title", ""),
                "file_id": node_dict["file_id"]
            }

            # Add type-specific info
            if current == "::ROOT":
                breadcrumb_item["type"] = "root"
            elif "::" not in current:
                # File-level node
                breadcrumb_item["type"] = "file"
                breadcrumb_item["module"] = node_dict["module"]

            breadcrumb.insert(0, breadcrumb_item)
            current = node_dict.get("parent_id", "")

        # Always ensure ::ROOT is at the start
        if not breadcrumb or breadcrumb[0]["id"] != "::ROOT":
            breadcrumb.insert(0, {
                "id": "::ROOT",
                "label": "ROOT",
                "type": "root",
                "title": "Knowledge Base Root",
                "file_id": ""
            })

        # Cache the result
        self._breadcrumb_cache[target_id] = breadcrumb
        return breadcrumb

    def unload_module(self, module_name: str) -> Dict[str, Any]:
        """Unload a module and clear associated caches.

        DEPRECATED: Module unloading is deprecated. The knowledge base now uses lazy loading
        and module caching for performance. Unloading modules is no longer necessary.

        Args:
            module_name: Name of the module to unload.
        """
        warnings.warn(
            "unload_module() is deprecated and will be removed in a future version. "
            "Module unloading is no longer necessary due to lazy loading and module caching.",
            DeprecationWarning,
            stacklevel=2
        )
        try:
            if not module_name:
                return {"success": False, "error": "No module specified"}

            target_module = module_name
            self.km.remove_module(target_module)
            # Clear caches
            self._node_cache.clear()
            self._breadcrumb_cache.clear()
            self.searcher.clear_cache()

            # If current node was in this module, move to root
            if self.current_node_id.startswith(target_module):
                self.current_node_id = "::ROOT"
                self.history = ["::ROOT"]
                self.history_cursor = 0

            return {"success": True, "module": target_module}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def purge(self) -> Dict[str, Any]:
        """Unload all modules and clear all caches.

        DEPRECATED: purge() is deprecated. The knowledge base now uses lazy loading
        and module caching for performance. Clearing all modules is no longer necessary.
        """
        warnings.warn(
            "purge() is deprecated and will be removed in a future version. "
            "Module purging is no longer necessary due to lazy loading and module caching.",
            DeprecationWarning,
            stacklevel=2
        )
        loaded = list(self.km.loaded_modules)
        for module in loaded:
            try:
                self.km.remove_module(module)
            except Exception:
                pass
        self._node_cache.clear()
        self._breadcrumb_cache.clear()
        self.current_node_id = "::ROOT"
        self.history = ["::ROOT"]
        self.history_cursor = 0
        return {"success": True, "unloaded": loaded}

    def navigate_back(self, steps: int = 1) -> Dict[str, Any]:
        """Navigate back in history N steps.

        Returns:
            Dictionary containing current position info
        """
        for _ in range(steps):
            if self.history_cursor <= 0:
                break

            # Move cursor back
            self.history_cursor -= 1
            target_id = self.history[self.history_cursor]

            # Get node without updating history
            target_dict = self._get_cached_or_build(target_id)
            if target_dict is None:
                # If node no longer exists, skip it
                self.history.pop(self.history_cursor)
                if self.history_cursor >= len(self.history):
                    self.history_cursor = len(self.history) - 1
                continue

            self.current_node_id = target_id

        return self.get_current_node()

    def navigate_forward(self, steps: int = 1) -> Dict[str, Any]:
        """Navigate forward in history N steps.

        Returns:
            Dictionary containing current position info
        """
        for _ in range(steps):
            if self.history_cursor >= len(self.history) - 1:
                break

            # Move cursor forward
            self.history_cursor += 1
            target_id = self.history[self.history_cursor]

            # Get node without updating history
            target_dict = self._get_cached_or_build(target_id)
            if target_dict is None:
                # If node no longer exists, skip it
                self.history.pop(self.history_cursor)
                self.history_cursor -= 1
                continue

            self.current_node_id = target_id

        return self.get_current_node()

    def up(self, levels: int = 1) -> Dict[str, Any]:
        """Navigate up N levels in the hierarchy."""
        last_res = {"success": True}
        for _ in range(levels):
            res = self.navigate_up()
            if "error" in res:
                return res
            last_res = res
        return last_res


    def get_history(self) -> Dict[str, Any]:
        """Get the current navigation history.

        Returns:
            Dict containing history list and cursor position
        """
        return {
            "items": self.history,
            "cursor": self.history_cursor,
            "size": len(self.history)
        }

    def get_current_node(self) -> Dict[str, Any]:
        """Get current navigation position information.

        Returns:
            Dictionary containing current position and history state
        """
        current_dict = self._get_cached_or_build(self.current_node_id)
        if current_dict is None:
            return {
                "error": {
                    "type": "current_node_invalid",
                    "message": "Current node is invalid"
                }
            }

        return {
            "type": "position_info",
            "current_node": self.current_node_id,
            "current_node_info": current_dict,
            "breadcrumb": self.get_breadcrumb(),
            "history_position": self.history_cursor,
            "history_size": len(self.history),
            "can_go_back": self.history_cursor > 0,
            "can_go_forward": self.history_cursor < len(self.history) - 1,
            "access_count": self._access_count.get(self.current_node_id, 0)
        }

    def search_nodes(self, query: Union[str, List[str]], search_under: Optional[str] = None, max_results: int = 50,
                     whole_word: bool = False, case_sensitive: bool = False, use_regex: bool = False,
                     order: str = "priority") -> Dict[str, Any]:
        """Search for nodes containing the query text(s) via NodeSearcher.

        Args:
            query: Search query text or list of query texts
            search_under: Optional root node ID to restrict search scope
            max_results: Maximum number of results to return
            whole_word: Whether to match whole words only
            case_sensitive: Whether the search is case sensitive
            use_regex: Whether to treat query as a regular expression
            order: "priority" or "dfs"

        Returns:
            Dictionary containing search results
        """
        # Resolve search_under if provided
        resolved_search_under = None
        if search_under:
            resolved = self._resolve_target_id(search_under)
            if "id" in resolved:
                resolved_search_under = resolved["id"]
            elif "error" in resolved:
                return {"error": {"type": "resolution_failed", "message": resolved["error"]}}
            elif resolved.get("type") == "ambiguous":
                return {
                    "type": "ambiguous_target",
                    "query": search_under,
                    "candidates": resolved["candidates"]
                }

        return self.searcher.search(
            query=query,
            search_under=resolved_search_under,
            max_results=max_results,
            whole_word=whole_word,
            case_sensitive=case_sensitive,
            use_regex=use_regex,
            order=order
        )

    def set_filter(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Update explorer filter options.

        Args:
            options: Dictionary of options to update

        Returns:
            Dictionary containing updated options
        """
        # Update only provided options
        for key, value in options.items():
            if hasattr(self.options, key):
                setattr(self.options, key, value)

        # Clear caches that might be affected
        self._node_cache.clear()
        self._breadcrumb_cache.clear()
        self.searcher.clear_cache()

        return {
            "type": "options_updated",
            "options": {
                "include_content": self.options.include_content,
                "include_see_also": self.options.include_see_also,
                "max_depth": self.options.max_depth,
                "content_preview_length": self.options.content_preview_length,
                "language": self.options.language,
                "exclude_modules": self.options.exclude_modules,
                "cache_size": self.options.cache_size
            }
        }

    def get_statistics(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about the knowledge base or a specific node.

        Args:
            node_id: Optional node ID to get statistics for (None for global stats)

        Returns:
            Dictionary containing statistics
        """
        if node_id is None:
            # Global statistics
            nodes = self.km.nodes
            total_nodes = len(nodes)
            section_nodes = sum(1 for node in nodes.values() if node["node_type"] == "section")
            content_nodes = sum(1 for node in nodes.values() if node["node_type"] == "content")

            # Count cross-references
            cross_refs = 0
            broken_links = 0
            for node in nodes.values():
                if node["node_type"] == "section":
                    cross_refs += len(node.get("see_also_id_descs", []))
                    for ref_id, _ in node.get("see_also_id_descs", []):
                        if self.km.get_node(ref_id) is None:
                            broken_links += 1
                elif node["node_type"] == "content":
                    cross_refs += len(node.get("inline_links", []))
                    for link_id in node.get("inline_links", []):
                        if self.km.get_node(link_id) is None:
                            broken_links += 1

            return {
                "type": "global_statistics",
                "total_nodes": total_nodes,
                "section_nodes": section_nodes,
                "content_nodes": content_nodes,
                "cross_references": cross_refs,
                "broken_links": broken_links,
                "module_coverage": {
                    "loaded": len(self.km.loaded_modules),
                    "total": len(self.km.available_modules)
                },
                "cache_stats": {
                    "cache_size": len(self._node_cache),
                    "cache_hits": sum(self._access_count.values()) - len(self._access_count),
                    "cache_misses": len(self._access_count),
                    "most_accessed": sorted(self._access_count.items(), key=lambda x: x[1], reverse=True)[:10]
                }
            }
        else:
            # Node-specific statistics
            target_id = self._expand_node_id(node_id)
            node_dict = self._get_cached_or_build(target_id)

            if node_dict is None:
                return {
                    "error": {
                        "type": "node_not_found",
                        "message": f"Node '{node_id}' not found under node '{self.current_node_id}'",
                        "node_id": node_id
                    }
                }

            stats = {
                "type": "node_statistics",
                "node_id": target_id,
                "access_count": self._access_count.get(target_id, 0),
                "cache_status": "cached" if target_id in self._node_cache else "not_cached"
            }

            if node_dict["type"] == "section":
                stats.update({
                    "child_count": node_dict["metadata"]["child_count"],
                    "has_see_also": node_dict["metadata"]["has_see_also"],
                    "see_also_count": node_dict["metadata"]["see_also_count"]
                })
            else:
                stats.update({
                    "content_length": node_dict["metadata"]["content_length"],
                    "link_count": node_dict["metadata"]["link_count"]
                })

            return stats

    def get_modules_info(self) -> Dict[str, Any]:
        """Get information about available and loaded modules."""
        return {
            "available": sorted(list(self.km.available_modules)),
            "loaded": sorted(list(self.km.loaded_modules))
        }

    def load_module(self, module_name: str) -> Dict[str, Any]:
        """Load a module via KnowledgeManager."""
        try:
            self.km.load_module(module_name)
            # Clear caches that might be affected by new nodes
            self._node_cache.clear()
            self._breadcrumb_cache.clear()
            self.searcher.clear_cache()
            # self._log(f"Module {module_name} loaded and caches cleared")
            return {"success": True, "module": module_name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_loaded_files(self) -> List[str]:
        """Get list of all loaded file IDs."""
        return sorted(list(self.km.loaded_files))

    def list_nodes(self, prefix: Optional[str] = None) -> List[Dict[str, str]]:
        """List nodes, optionally filtered by file prefix (supports wildcards)."""
        results = []

        # Determine effective pattern
        pattern = "*"
        if prefix:
            current_file = self.current_node_id.split('::')[0] if "::" in self.current_node_id else ""
            pattern = self.km.id_manager.resolve_relative_file_id(prefix, current_file)
            # If the resolved pattern doesn't have wildcards, assume it's a prefix
            if not any(c in pattern for c in "*?[]"):
                pattern += "*"

        nodes = self.km.nodes
        for node_id in sorted(nodes.keys()):
            if fnmatch.fnmatch(node_id, pattern):
                node = nodes[node_id]
                title = ""
                if node["node_type"] == "section":
                    title = node["title"]
                else:
                    title = node["content"][:50] + " ... ... " if len(node["content"]) > 50 else node["content"]

                results.append({
                    "node_id": node_id,
                    "type": "section" if node["node_type"] == "section" else "content",
                    "title": title
                })
        return results

    def get_loaded_roots(self) -> List[Dict[str, Any]]:
        """Get root nodes of all currently loaded modules.

        Returns:
            List of nodes with IDs like {module_name}::target
        """
        # self._log("Fetching root nodes for loaded modules")
        # Use KnowledgeManager's implementation which uses kb.root_nodes
        root_views = self.km.get_loaded_roots()
        # Convert to the format expected by this method
        results = []
        for node_view in root_views:
            if node_view:
                results.append(self._make_node_dict(node_view))
        return results
