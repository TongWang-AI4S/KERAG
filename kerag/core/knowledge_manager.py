"""Knowledge manager for KERAG system."""

import os
import warnings
from pathlib import Path
from typing import Dict, Optional, Set, List, Any
from kerag.core.id_manager import IDManager
# from kerag.core.nodes import Node  # This will be removed in next steps
from kerag.builder.knowledge_builder import KnowledgeBuilder
import yaml

class KnowledgeBase:
    """Internal data storage for knowledge nodes using a table-based approach.

    Attributes:
        base_info: Table mapping node_id to basic metadata
        extra_info: Table mapping node_id to type-specific content and references
        parent: Table mapping node_id to parent_id
        root_nodes: Set of node IDs that have no parent (ROOT)
    """
    def __init__(self):
        self.base_info: Dict[str, Dict[str, Any]] = {}
        self.extra_info: Dict[str, Dict[str, Any]] = {}
        self.parent: Dict[str, str] = {}
        self.root_nodes: Set[str] = set()  # Track nodes with parent as ROOT/none

    def add_node(self, node_id: str, node_type: str, file_id: str, module: str,
                 original_file_path: str, line_number: int, label: str):
        """
        Add a node to the knowledge base with basic information.
        Raises ValueError if node already exists.
        """
        if node_id in self.base_info:
            return
            # raise ValueError(f"Node already exists: {node_id}")

        base = {
            "node_type": node_type,
            "file_id": file_id,
            "module": module,
            "original_file_path": original_file_path,
            "line_number": line_number,
            "label": label
        }
        if node_type == "section":
            extra = {
                "title": "",
                "literal_level": None,
                "see_also_id_descs": [],
                "children_ids": []
            }
        else:
            extra = {
                "content": "",
                "inline_links": []
            }

        self.base_info[node_id] = base
        self.extra_info[node_id] = extra
        # 检查是否已存在父节点关系
        if node_id not in self.parent:
            self.parent[node_id] = "::ROOT"

    def update_section_info(self, node_id: str, title: str, literal_level: int):
        """Update section-specific information."""
        if node_id not in self.extra_info or self.base_info[node_id]["node_type"] != "section":
            raise ValueError(f"Invalid section node: {node_id}")
        self.extra_info[node_id]["title"] = title
        self.extra_info[node_id]["literal_level"] = literal_level

    def update_content_info(self, node_id: str, content: str, inline_links: List[str]):
        """Update content-specific information."""
        if node_id not in self.extra_info or self.base_info[node_id]["node_type"] != "content":
            raise ValueError(f"Invalid content node: {node_id}")
        self.extra_info[node_id]["content"] = content
        self.extra_info[node_id]["inline_links"] = inline_links

    def set_parent(self, node_id: str, parent_id: str):
        """Set the parent of a node. Only nodes with parent ::ROOT or null parents can be reset"""
        if node_id in self.parent and self.parent[node_id] != "" and self.parent[node_id] != "::ROOT":
            if parent_id != "" and parent_id != "::ROOT":
                raise ValueError(f"Parent node does not exist: {parent_id}")
        self.parent[node_id] = parent_id

    def add_child(self, parent_id: str, child_id: str):
        """Add a child to a section node."""
        if parent_id not in self.base_info:
             raise ValueError(f"Parent node does not exist: {parent_id}")
        if self.base_info[parent_id]["node_type"] != "section":
            raise ValueError(f"Cannot add child to non-section node: {parent_id}")

        children = self.extra_info[parent_id]["children_ids"]
        if child_id not in children:
            children.append(child_id)

    def set_child(self, parent_id: str, child_id: str):
        """Set a child node, combining parent and child relationship setup.

        This method consolidates set_parent and add_child operations:
        - Sets child's parent (unless ROOT/root)
        - Adds child to parent's children_ids
        - Handles special cases for ROOT/root parent
        - DOES NOT validate node existence (allows setting relationships before nodes are added)
        - Tracks root_nodes when parent is ROOT

        Args:
            parent_id: Parent node ID (can be "::ROOT", None, or empty string)
            child_id: Child node ID

        Raises:
            ValueError: If parent exists but is not a section node
        """
        # Handle root node tracking
        is_root_parent = (parent_id == "ROOT" or parent_id == "::ROOT" or parent_id is None or parent_id == "")

        # 检查子节点是否已经有实际的亲节点（非根节点）
        current_parent = self.parent.get(child_id, "")
        has_real_parent = current_parent and current_parent != "::ROOT" and current_parent != ""

        # 如果节点已经有实际亲节点，而新的父节点是根节点，则无视此操作
        if has_real_parent and is_root_parent:
            return

        # Remove from root_nodes if previously a root node
        if child_id in self.root_nodes and not is_root_parent:
            self.root_nodes.discard(child_id)

        # Add to root_nodes if parent is ROOT
        if is_root_parent:
            self.root_nodes.add(child_id)

        # Only validate parent IF it exists and is not ROOT
        if (not is_root_parent and
            parent_id in self.base_info and
            self.base_info[parent_id]["node_type"] != "section"):
            raise ValueError(f"Cannot add child to non-section node: {parent_id}")

        # Set parent relationship (special handling for ROOT)
        if not is_root_parent:
            self.parent[child_id] = parent_id

            # Add to parent's children (if parent exists)
            if parent_id in self.base_info:
                children = self.extra_info[parent_id]["children_ids"]
                if child_id not in children:
                    children.append(child_id)
        else:
            # For ROOT, only set parent without adding to children
            if is_root_parent:
                self.parent[child_id] = "::ROOT"


    def add_see_also(self, node_id: str, ref_id: str, description: str = ""):
        """Add a see-also reference to a section node."""
        if node_id not in self.base_info:
            raise ValueError(f"Node does not exist: {node_id}")
        if self.base_info[node_id]["node_type"] != "section":
             raise ValueError(f"Cannot add see-also to non-section node: {node_id}")

        see_also = self.extra_info[node_id]["see_also_id_descs"]
        see_also.append((ref_id, description))

    def get_node_view(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Return a unified view of a node's data."""
        if node_id not in self.base_info:
            return None

        view = {}
        view.update(self.base_info[node_id])
        view.update(self.extra_info[node_id])
        view["parent_id"] = self.parent.get(node_id, "")
        view["node_id"] = node_id
        return view

    def clear_files(self, file_ids: Set[str]):
        """Remove nodes belonging to specific file IDs."""
        to_remove = [
            nid for nid, info in self.base_info.items()
            if info["file_id"] in file_ids
        ]
        for nid in to_remove:
            self.base_info.pop(nid, None)
            self.extra_info.pop(nid, None)
            self.parent.pop(nid, None)


class KnowledgeManager:
    """Central manager for knowledge base modules and nodes.

    The KnowledgeManager orchestrates:
    - Module scanning and lazy loading
    - Node ID resolution and retrieval
    - Multi-language file support
    - Cross-file reference resolution

    Attributes:
        root: Root directory path of the knowledge base
        kb: KnowledgeBase instance storing node tables
        lang: Language preference for file loading
        available_modules: Set of available module names
        loaded_modules: Set of loaded module names
        loaded_files: Set of loaded file IDs
        id_manager: IDManager instance for ID operations
    """

    def __init__(self, local_root: Optional[str] = None, global_root: Optional[str] = None, lang: Optional[str] = None):
        """Initialize KnowledgeManager.

        Args:
            local_root: Local root directory for knowledge base (优先使用，如未提供则检查环境变量)
            global_root: Global root directory for knowledge base (优先使用，如未提供则检查环境变量)
            lang: Optional language preference (e.g., 'zh', 'en')(如不指定，检查环境变量 KERAG_LANG，默认为 "")

        Raises:
            ValueError: If local_root or specified paths are invalid
        """
        # Determine local root (priority: parameter > env var > default)
        if local_root:
            self.local_root = Path(local_root).resolve()
        else:
            # Check environment variable KERAG_LOCAL
            env_local_root = os.environ.get("KERAG_LOCAL")
            if env_local_root:
                self.local_root = Path(env_local_root).resolve()
            else:
                # Default to ./.kerag_modules
                self.local_root = Path.cwd() / ".kerag_modules"

        # Determine global root (priority: parameter > env var > default)
        if global_root:
            self.global_root = Path(global_root).resolve()
        else:
            # Check environment variable KERAG_HOME
            env_global_root = os.environ.get("KERAG_HOME")
            if env_global_root:
                self.global_root = Path(env_global_root).resolve()
            else:
                # Default to ~/.kerag_modules
                self.global_root = Path.home() / ".kerag_modules"

        # Determine language (priority: parameter > env var > default)
        if lang is not None:
            self.lang = lang
        else:
            self.lang = os.getenv("KERAG_LANG", "")

        # Validate that at least one root exists
        if not self.local_root.exists() and not self.global_root.exists():
            # Create local root for first-time setup
            self.local_root.mkdir(parents=True, exist_ok=True)

        self.kb = KnowledgeBase()
        self.available_modules: Dict[str, Path] = {}  # Module name -> root path
        self.loaded_modules: Set[str] = set()
        self.loaded_files: Set[str] = set()
        self.id_manager = IDManager(local_root=str(self.local_root), global_root=str(self.global_root), lang=self.lang)

        # Scan available modules
        self._scan_available_modules()

    @property
    def nodes(self) -> Dict[str, Any]:
        """Compatibility property for existing code (returns unified view dicts)."""
        return {nid: self.kb.get_node_view(nid) for nid in self.kb.base_info}

    def _scan_available_modules(self):
        """Scan both root directories for available modules from modules.yml.

        Modules are loaded from modules.yml in both global and local roots.
        Local modules take precedence over global ones.
        Raises FileNotFoundError if modules.yml is missing in an existing root.
        """

        # Helper to load modules from a root directory
        def load_modules_from_root(root_path: Path):
            config_path = root_path / "modules.yml"
            if not config_path.exists():
                # Auto-create empty modules.yml if not exists
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump({}, f)

            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}

                for module_name in config.keys():
                    module_path = root_path / module_name
                    if not module_path.is_dir():
                        continue

                    # Check if directory contains index.md or index.{lang}.md
                    index_exists = (
                        (module_path / "index.md").exists() or
                        (module_path / f"index.{self.lang}.md").exists()
                    )

                    if index_exists:
                        self.available_modules[module_name] = module_path

            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing {config_path}: {e}")

        # First scan global root
        if self.global_root.exists():
            load_modules_from_root(self.global_root)

        # Then scan local root - this will override global modules
        if self.local_root.exists():
            load_modules_from_root(self.local_root)

    def load_module(self, module: str):
        """Load a module into the knowledge base.

        Args:
            module: Module name (directory name)

        Raises:
            ValueError: If module not available
        """
        # Already loaded?
        if module in self.loaded_modules:
            return

        # Available?
        if module not in self.available_modules:
            raise ValueError(f"Module '{module}' not available")

        # Get the actual root path for this module
        module_root = self.available_modules[module]

        # Load module files
        # Don't pass root_path to preserve dual-root configuration in id_manager
        builder = KnowledgeBuilder(
            km=self,
            id_manager=self.id_manager
        )

        builder.build_module(module, base_path=str(module_root))

        # Track all files that were built
        built_files = builder.get_built_files()
        self.loaded_files.update(built_files)

        # Mark as loaded
        self.loaded_modules.add(module)

    def load_file(self, file_id: str):
        """Load a single file into the knowledge base.

        Args:
            file_id: File identifier (no leading "/")

        Raises:
            ValueError: If file doesn't exist
        """
        # Convert file_id to actual file path
        file_path = self.id_manager.file_id_to_path(file_id)
        if not file_path or not file_path.exists():
            raise ValueError(f"File not found for file_id: {file_id}")

        # Determine which root this file belongs to
        module_name = self._extract_module_from_file_id(file_id)
        if module_name and module_name in self.available_modules:
            module_root = self.available_modules[module_name]
        else:
            # Fallback to local root if module not found
            module_root = self.local_root

        builder = KnowledgeBuilder(
            km=self,
            id_manager=self.id_manager,
            root_path=str(module_root)
        )

        builder.build_file(str(file_path))

        # Track loaded file
        self.loaded_files.add(file_id)

        # Infer module from file_id
        module_name = self._extract_module_from_file_id(file_id)
        if module_name:
            self.loaded_modules.add(module_name)

    def _extract_module_from_file_id(self, file_id: str) -> Optional[str]:
        """Extract module name from file_id.

        Args:
            file_id: File identifier (no leading "/")

        Returns:
            Module name if extractable, None otherwise
        """
        if file_id:
            parts = file_id.split('/', 1)
            return parts[0]
        return None

    def get_node(self, node_id: str, current_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a node by ID with lazy loading support.

        Args:
            node_id: Node identifier
            current_file: Current file context

        Returns:
            Node data dictionary if found, None otherwise

        Raises:
            ValueError: For invalid paths during lazy loading
        """
        # Expand node ID fully first
        expanded_node_id = node_id
        if current_file is not None:
            expanded_node_id = self.id_manager.expand_node_id(node_id, current_file)

        # Extract file part for lazy loading
        file_part = expanded_node_id.split('::')[0]

        # Lazy loading
        if file_part == "":
            if "" not in self.loaded_files:
                try:
                    self.load_file("")
                except ValueError:
                    pass
        else:
            module_name = self._extract_module_from_file_id(file_part)
            if module_name and module_name not in self.loaded_modules:
                if module_name in self.available_modules:
                    try:
                        self.load_module(module_name)
                    except ValueError:
                        pass

        # Retrieve node view from KB
        return self.kb.get_node_view(expanded_node_id)

    def remove_module(self, module: str):
        """Remove all nodes belonging to a module.

        DEPRECATED: Module removal is deprecated. The knowledge base now uses lazy loading
        and module caching for performance. Removing modules is no longer necessary.

        Args:
            module: Module name

        Raises:
            ValueError: If module not loaded
        """
        warnings.warn(
            "remove_module() is deprecated and will be removed in a future version. "
            "Module removal is no longer necessary due to lazy loading and module caching.",
            DeprecationWarning,
            stacklevel=2
        )
        if module not in self.loaded_modules:
            raise ValueError(f"Module '{module}' not loaded")

        # Find files to remove
        prefix = module
        files_to_remove = set()

        for node_id in self.kb.base_info.keys():
            file_part = node_id.split('::')[0]
            if file_part == prefix or file_part.startswith(prefix + "/"):
                files_to_remove.add(file_part)

        # Clear from KnowledgeBase
        self.kb.clear_files(files_to_remove)

        # Remove from loaded files
        self.loaded_files -= files_to_remove

        # Remove from loaded modules
        self.loaded_modules.discard(module)

    def reload_module(self, module: str):
        """Reload a module.

        Args:
            module: Module name

        Raises:
            ValueError: If module not available
        """
        # Remove first
        try:
            self.remove_module(module)
        except ValueError:
            pass

        # Reload
        self.load_module(module)

    def get_nodes_from_file(self, file_id: str) -> Dict[str, Any]:
        """Get all nodes belonging to a specific file.

        Args:
            file_id: File identifier

        Returns:
            Dictionary of node_id -> node_data
        """
        result = {}

        for node_id, info in self.kb.base_info.items():
            if info["file_id"] == file_id:
                result[node_id] = self.kb.get_node_view(node_id)

        return result

    def get_nodes_from_module(self, module: str) -> Dict[str, Any]:
        """Get all nodes belonging to a specific module.

        Args:
            module: Module name

        Returns:
            Dictionary of node_id -> node_data
        """
        result = {}
        prefix = module

        for node_id, info in self.kb.base_info.items():
            file_id = info["file_id"]
            if file_id == prefix or file_id.startswith(prefix + "/"):
                result[node_id] = self.kb.get_node_view(node_id)

        return result

    def get_loaded_files(self) -> Set[str]:
        """Get all loaded file IDs.

        Returns:
            Set of all loaded file IDs
        """
        return self.loaded_files.copy()

    def get_loaded_roots(self) -> List[Dict[str, Any]]:
        """Get root nodes of all currently loaded modules.

        Returns:
            List of root node dictionaries (from kb.root_nodes)
        """
        return [self.kb.get_node_view(node_id) for node_id in self.kb.root_nodes]

    def list_directory_contents(self, current_file_id: str) -> List[Dict[str, Any]]:
        """List contents of the directory containing the specified file.

        For root directory ("") or files directly under root, returns all available modules.
        For files within a module, returns all loaded files in the same directory.

        Args:
            current_file_id: File identifier to determine the directory

        Returns:
            List of directory contents, each item containing:
            - type: "module", "submodule" or "file"
            - id: file_id
            - name: display name
        """
        result = []


        # Check if current file is an index file
        if self.id_manager._is_index_file(current_file_id):
            # For index files, use the file_id itself as the directory prefix
            dir_prefix = current_file_id
        else:
            # For non-index files, get the parent directory
            # Remove the last component to get directory
            if "/" in current_file_id:
                dir_prefix = current_file_id.rsplit("/", 1)[0]
            else:
                dir_prefix = ""
        # Handle root directory (only return modules, no files allowed in root)
        if dir_prefix == "":
            # Return all available modules
            for module in sorted(self.available_modules):
                result.append({
                    "type": "module",
                    "id": module,
                    "name": module
                })
            return result

        # Find all loaded files in the same directory
        dir_files = set()
        for file_id in self.loaded_files:
            # Check if file is in the same directory
            if file_id == dir_prefix:
                # This is the index file of this directory
                dir_files.add(file_id)
            elif file_id.startswith(dir_prefix + "/"):
                # Check if it's a direct child (no more slashes after prefix)
                remaining = file_id[len(dir_prefix + "/"):]
                if "/" not in remaining:
                    dir_files.add(file_id)

        # Add sorted results
        for file_id in sorted(dir_files):
            # Determine display name
            if self.id_manager._is_index_file(file_id):
                file_type = "module"
            else:
                file_type = "file"

            name = file_id.split("/")[-1]

            result.append({
                "type": file_type,
                "id": file_id,
                "name": name
            })

        return result