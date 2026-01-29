"""Namespace management for KERAG document parsing."""

import os
import re
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path


class IDManager:
    """Manages namespaces for KERAG document parsing.

    The IDManager is responsible for:
    - Generating unique node IDs
    - Converting between file paths and file_ids
    """

    def __init__(self, local_root: Optional[str] = None, global_root: Optional[str] = None, lang: str = ''):
        """Initialize the namespace manager.

        Args:
            local_root: Optional local root path for knowledge base.
            global_root: Optional global root path for knowledge base.
            lang: Optional language prefix (e.g., 'zh', 'en').
        """
        self._node_id_counter: Dict[str, int] = {}
        self._current_file: Optional[str] = None
        self._local_root: Optional[Path] = Path(local_root).resolve() if local_root else None
        self._global_root: Optional[Path] = Path(global_root).resolve() if global_root else None
        self.lang: str = lang

        # Cache dictionaries for path conversions
        self._path_to_file_id_cache: Dict[str, str] = {}
        self._file_id_to_path_cache: Dict[str, Optional[str]] = {}
        self._module_to_root_cache: Dict[str, Path] = {}  # Maps module (e.g., "physics") to its determined root Path

    def generate_node_id(self, label: Optional[str] = None,
                        file_id: Optional[str] = None,
                        file_node_count: Optional[int] = 0) -> str:
        """Generate a unique node ID.

        Args:
            label: Optional label to base the ID on
            file_id: File identifier (relative path from root)
            file_node_count: Current node count for this file (for unlabeled nodes)

        Returns:
            Unique node ID
        """
        if label:
            # Use file_id::label format
            return f"{file_id}::{label}"
        else:
            # Use file_id::__node_N format
            return f"{file_id}::__node_{file_node_count}"

    def _is_index_file(self, file_id: str) -> bool:
        """Check if a file_id points to an index file.

        Args:
            file_id: File identifier (starts with "/")

        Returns:
            True if the file_id points to an index file
        """
        try:
            path = self.file_id_to_path(file_id)
            if path:
                return path.name.startswith('index')
            return False
        except:
            return False

    def resolve_relative_file_id(self, path_ref: str, current_file_id: str) -> str:
        """Resolve a relative path reference to a file_id.

        Handles all path symbols: %env%, / (root), .. (parent), . (current)
        Returns a file_id that does NOT start with "/".

        Args:
            path_ref: Path reference to resolve (e.g., "../sibling", "./sub", "file")
            current_file_id: Current file's file_id for relative resolution (no leading "/")

        Returns:
            Resolved file_id (no leading "/")
        """
        # print(f"[DEBUG] resolve_relative_file_id: path_ref='{path_ref}', current_file_id='{current_file_id}'")  # DEBUG

        if not path_ref:
            path_ref = '.'
        elif path_ref == 'index':
            path_ref = '.'
        elif path_ref.endswith('/index'):
            path_ref = path_ref[:-6]

        # Handle environment variable expansion (%ENV%/path)
        if path_ref.startswith('%'):
            env_match = re.match(r'%([^%]+)%(.*)', path_ref)
            if env_match and hasattr(self, '_root_path') and self._root_path:
                env_var, remaining_path = env_match.groups()
                env_value = os.environ.get(env_var, '')
                if env_value:
                    # Create absolute path and convert to file_id
                    abs_path = Path(env_value) / remaining_path.lstrip('/')
                    return self.path_to_file_id(str(abs_path))
            return path_ref.lstrip('/')  # Unresolvable env var, just cleanup

        # Handle root-relative path (/path/from/root)
        if path_ref.startswith('/'):
            result = path_ref.lstrip('/')
            # print(f"[DEBUG] resolve_relative_file_id: Root-relative path, returning: {result}")  # DEBUG
            return result

        # Handle relative path (.., ., or plain relative)
        # If no leading path symbol, implement new fallback logic
        if not any(path_ref.startswith(s) for s in ('.', '..', '/')):
            # Rule: Try relative to current_dir first
            rel_result = self._resolve_basic_relative(path_ref, current_file_id)

            # Check if this file actually exists (relative to current)
            if rel_result and self.file_id_to_path(rel_result):
                # print(f"[DEBUG] resolve_relative_file_id: Found relative file: {rel_result}")  # DEBUG
                return rel_result

            # Check if path_ref itself is an available module or exists at root
            # This handles jumping from 'ai' to 'physics' top-level
            if self.file_id_to_path(path_ref):
                 # print(f"[DEBUG] resolve_relative_file_id: Found root-relative fallback: {path_ref}")  # DEBUG
                 return path_ref

            # Default back to the relative result
            return rel_result

        return self._resolve_basic_relative(path_ref, current_file_id)

    def _resolve_basic_relative(self, path_ref: str, current_file_id: str) -> str:
        """Original relative resolution logic, now internal."""
        # Get directory of current file (handle index files)
        is_index = self._is_index_file(current_file_id) if current_file_id else True

        if is_index or current_file_id.endswith('/index'):
            current_dir = current_file_id
        elif '/' in current_file_id:
            current_dir = current_file_id[:current_file_id.rindex('/')]
        else:
            current_dir = ""

        # Build the target path
        if current_dir:
            target = current_dir + '/' + path_ref
        else:
            target = path_ref

        # Normalize the path (resolve .. and .)
        parts = []
        for part in target.split('/'):
            if part == '' or part == '.':
                continue
            elif part == '..':
                if parts:
                    parts.pop()
            else:
                parts.append(part)

        result = '/'.join(parts)
        return result

    def expand_node_id(self, node_id: str, current_file_id: Optional[str] = None) -> str:
        """Expand a node ID with relative file references.

        Handles node_id in formats:
        - "file_id::label" - Full reference with possible relative path in file_id
        - "label" - Current file label (adds current_file_id::)

        Args:
            node_id: Node ID to expand
            current_file_id: Current file's file_id for relative resolution (no leading "/")

        Returns:
            Expanded node ID with resolved file_part
        """
        # print(f"[DEBUG] expand_node_id: node_id='{node_id}', current_file_id='{current_file_id}'")  # DEBUG

        # If contains ::, resolve the file_part
        if '::' in node_id:
            file_part, label_part = node_id.split('::', 1)
            # print(f"[DEBUG] expand_node_id: Split into file_part='{file_part}', label_part='{label_part}'")  # DEBUG
            # Resolve file_part to file_id (handles %, /, .., ., etc)
            resolved_file = self.resolve_relative_file_id(file_part, current_file_id or '')
            result = f"{resolved_file}::{label_part}"
            # print(f"[DEBUG] expand_node_id: Resolved to '{result}'")  # DEBUG
            return result

        # No ::, treat as label in current file
        if current_file_id is not None:
            result = f"{current_file_id}::{node_id}"
            # print(f"[DEBUG] expand_node_id: Label in current file, result='{result}'")  # DEBUG
            return result

        # No context, return as-is
        # print(f"[DEBUG] expand_node_id: No context, returning as-is: '{node_id}'")  # DEBUG
        return node_id

    def set_root_path(self, local_root: Optional[str] = None, global_root: Optional[str] = None, lang: Optional[str] = None):
        """Set the root paths for file_id conversions.

        Args:
            local_root: Local root directory for knowledge base
            global_root: Global root directory for knowledge base (fallback)
            lang: Optional language prefix (e.g., 'zh', 'en'). If None, keeps existing language.
        """
        # print(f"[DEBUG] set_root_path: local_root={local_root}, global_root={global_root}, lang={lang}")  # DEBUG
        # print(f"[DEBUG] set_root_path: Before clear - path_cache={len(self._path_to_file_id_cache)}, file_cache={len(self._file_id_to_path_cache)}, module_cache={len(self._module_to_root_cache)}")  # DEBUG

        # Clear all caches before changing roots
        self._path_to_file_id_cache.clear()
        self._file_id_to_path_cache.clear()
        self._module_to_root_cache.clear()

        # print(f"[DEBUG] set_root_path: After clear - path_cache={len(self._path_to_file_id_cache)}, file_cache={len(self._file_id_to_path_cache)}, module_cache={len(self._module_to_root_cache)}")  # DEBUG

        if local_root is not None:
            self._local_root = Path(local_root).resolve()
            # print(f"[DEBUG] set_root_path: Set local_root to {self._local_root}")  # DEBUG
        if global_root is not None:
            self._global_root = Path(global_root).resolve()
            # print(f"[DEBUG] set_root_path: Set global_root to {self._global_root}")  # DEBUG
        if lang is not None:
            self.lang = lang
            # print(f"[DEBUG] set_root_path: Set lang to '{lang}'")  # DEBUG

        # print(f"[DEBUG] set_root_path: Final roots - local_root={self._local_root}, global_root={self._global_root}")  # DEBUG

    def path_to_file_id(self, path: str) -> str:
        """Convert a file path to file_id (no leading "/").

        Args:
            path: Path to convert (absolute or relative)

        Returns:
            File identifier (no leading "/")

        Raises:
            ValueError: If path is not under any root
        """
        # Check cache first
        if path in self._path_to_file_id_cache:
            return self._path_to_file_id_cache[path]

        # Convert to Path and resolve
        file_path = Path(path).resolve()

        # Determine which root this path belongs to
        # First, check if this module's root is already cached
        module = None
        root_to_use = None
        if self._local_root or self._global_root:
            # Extract module name from path
            try:
                if self._local_root and file_path.is_relative_to(self._local_root):
                    rel_path = file_path.relative_to(self._local_root)
                    module_parts = str(rel_path).split(os.sep)
                    module = module_parts[0] if module_parts and module_parts[0] else None
                    # Check cache
                    if module and module in self._module_to_root_cache:
                        root_to_use = self._module_to_root_cache[module]
                        # print(f"[DEBUG] path_to_file_id: Using cached root for module '{module}': {root_to_use}")  # DEBUG
                    else:
                        root_to_use = self._local_root
                        # print(f"[DEBUG] path_to_file_id: Using local_root for module '{module}': {root_to_use}")  # DEBUG
                elif self._global_root and file_path.is_relative_to(self._global_root):
                    rel_path = file_path.relative_to(self._global_root)
                    module_parts = str(rel_path).split(os.sep)
                    module = module_parts[0] if module_parts and module_parts[0] else None
                    # Check cache
                    if module and module in self._module_to_root_cache:
                        root_to_use = self._module_to_root_cache[module]
                        # print(f"[DEBUG] path_to_file_id: Using cached root for module '{module}': {root_to_use}")  # DEBUG
                    else:
                        root_to_use = self._global_root
                        # print(f"[DEBUG] path_to_file_id: Using global_root for module '{module}': {root_to_use}")  # DEBUG
                else:
                    # Path not under any root
                    raise ValueError("Path is not under any root directory")
            except ValueError:
                # Path not under any root
                raise ValueError("Path is not under any root directory")
        else:
            raise ValueError("No root paths configured in IDManager")

        # Cache module root only if this is an actual file (not a hypothetical path)
        if module and module not in self._module_to_root_cache and root_to_use and file_path.exists():
            self._module_to_root_cache[module] = root_to_use
            # print(f"[DEBUG] path_to_file_id: Cached module '{module}' -> {root_to_use}")  # DEBUG

        # Get relative path from root
        rel_path = file_path.relative_to(root_to_use)

        # Convert to string with forward slashes
        rel_path_str = str(rel_path).replace(os.sep, '/')

        # Remove .md extension
        if rel_path_str.endswith('.md'):
            rel_path_str = rel_path_str[:-3]

        # Remove language suffix if present
        if self.lang and rel_path_str.endswith(f'.{self.lang}'):
            rel_path_str = rel_path_str[:-(len(self.lang) + 1)]

        # Special handling for index files
        if rel_path_str.endswith('/index'):
            rel_path_str = rel_path_str[:-6]  # Remove /index
        elif rel_path_str == 'index':
            rel_path_str = ''

        # Construct file_id (no leading "/")
        file_id = rel_path_str

        # Cache the result
        self._path_to_file_id_cache[path] = file_id

        return file_id

    def _try_resolve(self, rel_path, root_dir: Path) -> Optional[Path]:
        if not root_dir:
            # print(f"[DEBUG] _try_resolve: No root_dir provided")  # DEBUG
            return None
        base_path = root_dir / rel_path.replace('/', os.sep)
        # print(f"[DEBUG] _try_resolve: root_dir={root_dir}, rel_path='{rel_path}', base_path={base_path}")  # DEBUG

        paths_to_try = []

        if base_path.is_dir():
            # print(f"[DEBUG] _try_resolve: base_path is a directory")  # DEBUG
            if self.lang:
                paths_to_try.append(base_path / f"index.{self.lang}.md")
                # print(f"[DEBUG] _try_resolve: Added path to try: {base_path / f'index.{self.lang}.md'}")  # DEBUG
            paths_to_try.append(base_path / "index.md")
            # print(f"[DEBUG] _try_resolve: Added path to try: {base_path / 'index.md'}")  # DEBUG
        else:
            # print(f"[DEBUG] _try_resolve: base_path is a file path")  # DEBUG
            if self.lang:
                lang_path = Path(f"{base_path}.{self.lang}.md")
                paths_to_try.append(lang_path)
                # print(f"[DEBUG] _try_resolve: Added path to try: {lang_path}")  # DEBUG
            md_path = Path(f"{base_path}.md")
            paths_to_try.append(md_path)
            # print(f"[DEBUG] _try_resolve: Added path to try: {md_path}")  # DEBUG

            if self.lang:
                index_lang_path = base_path / f"index.{self.lang}.md"
                paths_to_try.append(index_lang_path)
                # print(f"[DEBUG] _try_resolve: Added path to try: {index_lang_path}")  # DEBUG
            index_path = base_path / "index.md"
            paths_to_try.append(index_path)
            # print(f"[DEBUG] _try_resolve: Added path to try: {index_path}")  # DEBUG

        for path in paths_to_try:
            # print(f"[DEBUG] _try_resolve: Checking path: {path}, exists={path.exists()}")  # DEBUG
            if path.exists():
                # print(f"[DEBUG] _try_resolve: Found existing path: {path}")  # DEBUG
                return path

        # print(f"[DEBUG] _try_resolve: No existing path found for rel_path='{rel_path}'")  # DEBUG
        return None

    def file_id_to_path(self, file_id: str) -> Optional[Path]:
        """Convert file_id to file path for lookup (checking language versions first).

        Args:
            file_id: File identifier (no leading "/")

        Returns:
            Path to the file if found, None otherwise

        Raises:
            ValueError: If no root paths are configured
        """
        # print(f"[DEBUG] file_id_to_path: Processing file_id='{file_id}'")  # DEBUG

        if not (self._local_root or self._global_root):
            raise ValueError("No root paths configured in IDManager")

        # Check cache first
        if file_id in self._file_id_to_path_cache:
            result = self._file_id_to_path_cache[file_id]
            # print(f"[DEBUG] file_id_to_path: Cache hit for '{file_id}' -> {result}")  # DEBUG
            if result:
                return Path(result)
            return None

        # Clean up leading slash if accidentally provided
        rel_path = file_id.lstrip('/')

        # Extract module from file_id to use cached root if available
        module = None
        if rel_path:
            module_parts = rel_path.split('/')
            module = module_parts[0] if module_parts[0] else None
            # print(f"[DEBUG] file_id_to_path: Extracted module='{module}' from file_id='{file_id}'")  # DEBUG

        # Try cached module root first if available
        resolved_path = None
        if module and module in self._module_to_root_cache:
            # Use the cached root for this module
            cached_root = self._module_to_root_cache[module]
            # print(f"[DEBUG] file_id_to_path: Using cached root for module '{module}': {cached_root}")  # DEBUG
            resolved_path = self._try_resolve(rel_path, cached_root)

        # If not found, try both roots and update cache
        if not resolved_path:
            if self._local_root:
                # print(f"[DEBUG] file_id_to_path: Trying local_root for module '{module}'")  # DEBUG
                resolved_path = self._try_resolve(rel_path, self._local_root)
                # if resolved_path:
                    # print(f"[DEBUG] file_id_to_path: Found in local_root: {resolved_path}")  # DEBUG
            if not resolved_path and self._global_root:
                # print(f"[DEBUG] file_id_to_path: Trying global_root for module '{module}'")  # DEBUG
                resolved_path = self._try_resolve(rel_path, self._global_root)

                # If found in global root, update module cache
                if resolved_path and module and module not in self._module_to_root_cache:
                    self._module_to_root_cache[module] = self._global_root
                    # print(f"[DEBUG] file_id_to_path: Cached module '{module}' -> global_root")  # DEBUG
            elif resolved_path and module and module not in self._module_to_root_cache:
                # If found in local root, update module cache
                self._module_to_root_cache[module] = self._local_root
                # print(f"[DEBUG] file_id_to_path: Cached module '{module}' -> local_root")  # DEBUG

        # Cache the result
        result = str(resolved_path) if resolved_path else None
        self._file_id_to_path_cache[file_id] = result
        # print(f"[DEBUG] file_id_to_path: Final result for '{file_id}' -> {result}")  # DEBUG

        return resolved_path

    def get_files_in_directory(self, dir_file_id: str) -> List[str]:
        """Get all file IDs in a directory, filtering by language preference.

        Args:
            dir_file_id: Directory file ID (e.g., "module1" or "module1/subdir")

        Returns:
            List of file IDs in the directory, filtered by language preference
        """
        # Check if any root is available
        if not (self._local_root or self._global_root):
            return []

        # Convert file ID to directory path
        dir_path = self.file_id_to_path(dir_file_id)
        if dir_path and dir_path.is_file():
            dir_path = dir_path.parent
        if not dir_path or not dir_path.is_dir():
            return []

        seen_ids = set()

        # Part 1: All markdown files in the directory (recursive)
        for md_file in dir_path.rglob("*.md"):
            # Get the actual file path
            actual_path = str(md_file)

            # Convert to file_id (this handles language preference automatically)
            file_id = self.path_to_file_id(actual_path)
            if file_id is None or file_id in seen_ids:
                # Skip if we've already seen this file_id
                continue

            # Language filtering: skip files with language suffix that don't match current language
            if self.lang:
                # If file has language suffix that's not current language, skip it
                if '.' in file_id.split('/')[-1] and not file_id.endswith(f'.{self.lang}'):
                    continue
            else:
                # If no language preference, skip files with language suffix
                if '.' in file_id.split('/')[-1]:
                    continue

            seen_ids.add(file_id)

        return sorted(seen_ids)

    def path_to_module(self, file_path: str) -> str:
        """Convert file path to module path.

        Args:
            file_path: File path

        Returns:
            Module path
        """
        file_id = self.path_to_file_id(file_path)
        if not file_id:
            return ""
        return file_id.split('/')[0]

    def clear(self):
        """Clear the ID manager state."""
        self._node_id_counter.clear()
        self._current_file = None
