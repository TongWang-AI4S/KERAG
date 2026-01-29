import os
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
import tarfile
import yaml
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from .metadata import parse_modules_txt_line, extract_from_kerag_meta, extract_from_index_md

class ModuleManager:
    """Manages KERAG modules in global and local scopes."""

    def __init__(self, local_root: Optional[str] = None, global_root: Optional[str] = None):
        """
        Initialize ModuleManager.

        Args:
            local_root: Local root directory (优先使用，如未提供则检查环境变量，默认为 ./.kerag_modules)
            global_root: Global root directory (优先使用，如未提供则检查环境变量，默认为 ~/.kerag_modules)
        """
        self.global_root = self._get_global_root(global_root)
        self.local_root = self._get_local_root(local_root)
        self.ensure_global_init()
        self.ensure_local_init()

    def _get_global_root(self, global_root: Optional[str] = None) -> Path:
        """Get the global KERAG_HOME path."""
        # Priority: parameter > env var > default
        if global_root:
            return Path(global_root).expanduser().resolve()

        env_home = os.environ.get("KERAG_HOME")
        if env_home:
            return Path(env_home).expanduser().resolve()
        return Path.home() / ".kerag_modules"

    def _get_local_root(self, local_root: Optional[str] = None) -> Path:
        """Get the local .kerag_modules path."""
        # Priority: parameter > env var > default
        if local_root:
            return Path(local_root).resolve()

        env_local = os.environ.get("KERAG_LOCAL")
        if env_local:
            return Path(env_local).resolve()
        return Path.cwd() / ".kerag_modules"

    def ensure_global_init(self):
        """Initialize global directory if it doesn't exist."""
        if not self.global_root.exists():
            self.global_root.mkdir(parents=True, exist_ok=True)
            index_path = self.global_root / "index.md"
            if not index_path.exists():
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write("# ROOT [@ROOT]\n\n<!-- PLEASE LEAVE THIS FILE AS IS -->\n\n")

        self._migrate_if_needed(self.global_root)
        modules_yml = self.global_root / "modules.yml"
        if not modules_yml.exists():
            self._write_modules_yml(modules_yml, {})

    def ensure_local_init(self):
        """Initialize local directory if it doesn't exist."""
        if not self.local_root.exists():
            self.local_root.mkdir(parents=True, exist_ok=True)

        self._migrate_if_needed(self.local_root)
        modules_yml = self.local_root / "modules.yml"
        if not modules_yml.exists():
            self._write_modules_yml(modules_yml, {})

    def _migrate_if_needed(self, root: Path):
        """将 modules.txt 迁移到 modules.yml"""
        old_path = root / "modules.txt"
        new_path = root / "modules.yml"
        if old_path.exists() and not new_path.exists():
            modules = self._read_modules_txt(old_path)
            yml_data = {}
            for name, version in modules:
                yml_data[name] = {"version": version} if version else {}

            self._write_modules_yml(new_path, yml_data)
            old_path.unlink()

    def get_modules(self, scope: str = "both") -> Dict[str, Dict[str, Dict[str, Any]]]:
        """List modules in specified scope."""
        result = {}
        if scope in ("global", "both"):
            result["global"] = self._read_modules_yml(self.global_root / "modules.yml")
        if scope in ("local", "both"):
            result["local"] = self._read_modules_yml(self.local_root / "modules.yml")
        return result

    def _read_modules_yml(self, path: Path) -> Dict[str, Dict[str, Any]]:
        """读取 modules.yml"""
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_modules_yml(self, path: Path, modules: Dict[str, Dict[str, Any]]):
        """写入 modules.yml"""
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(modules, f, allow_unicode=True, sort_keys=True)

    def _read_modules_txt(self, path: Path) -> List[Tuple[str, Optional[str]]]:
        """读取旧格式 modules.txt (仅用于迁移)"""
        if not path.exists():
            return []
        modules = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parsed = parse_modules_txt_line(line)
                if parsed:
                    modules.append(parsed)
        return modules

    def _identify_module_dir(self, temp_dir: Path) -> Tuple[Optional[str], Optional[Path]]:
        """Identify the module directory and its name from a temporary location."""
        items = [i for i in temp_dir.iterdir() if i.name != "__MACOSX"] # Ignore Mac junk

        # Check for kerag_meta.txt
        meta_file = temp_dir / "kerag_meta.txt"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line:
                    target = temp_dir / first_line
                    if target.exists() and target.is_dir():
                        return first_line, target

        # Check if there is only one directory
        dirs = [i for i in items if i.is_dir()]
        if len(dirs) == 1:
            return dirs[0].name, dirs[0]

        # Fallback: use the temp_dir itself if it contains .md files?
        # Or just return None if ambiguous
        return None, None

    def _extract_module_metadata_from_install(self, temp_dir: Path, module_src_path: Path) -> Tuple[str, Optional[str], Optional[str]]:
        """从安装源提取元数据（仅在 install 过程中调用）

        优先级（index.md 覆盖 kerag_meta.txt）：
        1. temp_dir/kerag_meta.txt（第一行的 name=version，以及 Description:）- 可选
        2. module_src_path/index.md（<!-- Module: -->、<!-- Version: --> 和注释描述）- 优先
        3. module_src_path.name（默认值，无版本）

        返回:
            Tuple[str, Optional[str], Optional[str]]: (模块名称, 版本, 描述)
        """
        # 1. 从 kerag_meta.txt 提取（可选）
        meta_name, meta_version, meta_desc = None, None, None
        meta_path = temp_dir / "kerag_meta.txt"
        if meta_path.exists():
            meta_name, meta_version, meta_desc = extract_from_kerag_meta(meta_path)

        # 2. 从 index.md 提取（优先）
        index_name, index_version, index_desc = None, None, None
        index_path = module_src_path / "index.md"
        if index_path.exists():
            index_name, index_version, index_desc = extract_from_index_md(index_path)

        # 3. 确定最终名称、版本和描述
        final_name = index_name or meta_name or module_src_path.name
        final_version = index_version or meta_version
        final_desc = index_desc or meta_desc

        return final_name, final_version, final_desc

    def install(self, source: str, global_scope: bool = False, force: bool = False) -> Tuple[bool, str]:
        """Install a module from source."""
        target_root = self.global_root if global_scope else self.local_root
        if global_scope:
            self.ensure_global_init()
        else:
            self.ensure_local_init()

        modules_yml_path = target_root / "modules.yml"
        current_modules = self._read_modules_yml(modules_yml_path)

        with tempfile.TemporaryDirectory() as tmp_str:
            tmp_path = Path(tmp_str)
            module_name = None
            module_src_path = None

            # 1. Download/Clone/Copy to tmp
            try:
                # ... (保持原有的下载逻辑不变)
                if source.startswith("git+"):
                    repo_url = source[4:]
                    print(f"Cloning module from {repo_url}...")
                    subprocess.run(["git", "clone", repo_url, tmp_str], check=True, capture_output=True)
                    shutil.rmtree(tmp_path / ".git", ignore_errors=True)
                elif source.startswith(("http://", "https://")):
                    ext = source.split("?")[0].split(".")[-1]
                    archive_path = tmp_path / f"download.{ext}"
                    print(f"Downloading module from {source}...")
                    urllib.request.urlretrieve(source, archive_path)

                    if zipfile.is_zipfile(archive_path):
                        print(f"Extracting ZIP archive...")
                        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                            zip_ref.extractall(tmp_path)
                        os.remove(archive_path)
                    elif tarfile.is_tarfile(archive_path):
                        print(f"Extracting TAR archive...")
                        with tarfile.open(archive_path, 'r:*') as tar_ref:
                            tar_ref.extractall(tmp_path)
                        os.remove(archive_path)
                    else:
                        return False, f"Unsupported archive format: {ext}"
                elif Path(source).is_file() and (tarfile.is_tarfile(source) or zipfile.is_zipfile(source)):
                    source_path = Path(source)
                    print(f"Installing from local archive: {source_path.name}...")
                    if zipfile.is_zipfile(source_path):
                        with zipfile.ZipFile(source_path, 'r') as zip_ref:
                            zip_ref.extractall(tmp_path)
                    elif tarfile.is_tarfile(source_path):
                        with tarfile.open(source_path, 'r:*') as tar_ref:
                            tar_ref.extractall(tmp_path)
                    else:
                        return False, f"Unsupported archive format: {source_path.suffix}"
                elif Path(source).is_dir():
                    source_path = Path(source)
                    print(f"Installing from local directory: {source_path.name}...")
                    shutil.copytree(source, tmp_path, dirs_exist_ok=True)
                else:
                    return False, f"Invalid source or module name: {source}. Direct names not supported yet."

                # 2. Identify module
                module_name, module_src_path = self._identify_module_dir(tmp_path)
                if not module_name or not module_src_path:
                    return False, "Could not identify module directory. Ensure it has a single subfolder or kerag_meta.txt."

                # 从安装源提取元数据
                final_name, final_version, final_desc = self._extract_module_metadata_from_install(tmp_path, module_src_path)

                # 3. Check for existing
                dest_path = target_root / final_name
                if dest_path.exists():
                    if not force:
                        return False, f"CONFLICT:{final_name}"
                    shutil.rmtree(dest_path)

                # 4. Copy to destination
                shutil.copytree(module_src_path, dest_path)

                # 5. Update modules.yml
                module_info = {}
                if final_version: module_info["version"] = final_version
                if final_desc: module_info["description"] = final_desc

                current_modules[final_name] = module_info
                self._write_modules_yml(modules_yml_path, current_modules)

                return True, final_name

            except Exception as e:
                return False, str(e)

    def remove(self, module_name: str, scope: str = "both") -> List[Tuple[str, bool, str]]:
        """Remove a module from specified scope(s)."""
        results = [] # List of (scope, success, message)

        scopes_to_check = []
        if scope == "both":
            scopes_to_check = [("global", self.global_root), ("local", self.local_root)]
        elif scope == "global":
            scopes_to_check = [("global", self.global_root)]
        elif scope == "local":
            scopes_to_check = [("local", self.local_root)]

        for s_name, s_root in scopes_to_check:
            dest_path = s_root / module_name
            modules_yml_path = s_root / "modules.yml"

            if not dest_path.exists():
                results.append((s_name, False, "Not found"))
                continue

            try:
                if dest_path.is_dir():
                    shutil.rmtree(dest_path)
                else:
                    os.remove(dest_path)

                # Update modules.yml
                current = self._read_modules_yml(modules_yml_path)
                if module_name in current:
                    del current[module_name]
                    self._write_modules_yml(modules_yml_path, current)

                results.append((s_name, True, "Removed"))
            except Exception as e:
                results.append((s_name, False, str(e)))

        return results

    def _extract_module_metadata_from_scan(self, module_path: Path) -> Tuple[str, Optional[str], Optional[str]]:
        """从已安装的模块提取元数据（仅在 scan 过程中调用）"""
        index_path = module_path / "index.md"
        if index_path.exists():
            name, version, desc = extract_from_index_md(index_path)
            # 使用目录名作为模块名（如果index中没有指定Module）
            final_name = name if name else module_path.name
            return final_name, version, desc

        return module_path.name, None, None

    def scan(self, scope: str = "local") -> Tuple[List[Tuple[str, Optional[str], Optional[str]]], List[str], Path]:
        """扫描目录并检测所有模块的元数据变化，保持原有顺序。"""
        target_root = self.global_root if scope == "global" else self.local_root
        modules_yml_path = target_root / "modules.yml"
        current_modules = self._read_modules_yml(modules_yml_path)

        found_module_names = []
        found_module_metadata = {}

        for item in target_root.iterdir():
            if item.is_dir() and item.name != "__pycache__":
                indices = list(item.glob("index.md")) + list(item.glob("index.*.md"))
                if indices:
                    name, version, desc = self._extract_module_metadata_from_scan(item)
                    found_module_metadata[name] = (version, desc)
                    found_module_names.append(name)

        # 检查所有发现的模块（包括新模块）
        to_update = []
        for name, (version, desc) in found_module_metadata.items():
            # 新发现的模块（不在 current_modules 中）
            if name not in current_modules:
                to_update.append((name, version, desc))
            else:
                # 已存在的模块，检查元数据是否有变化
                current_info = current_modules[name]
                current_version = current_info.get("version")
                current_desc = current_info.get("description")

                # 将 None 和空字符串视为相同，避免无效更新
                norm_version = version or None
                norm_current_version = current_version or None
                norm_desc = desc or None
                norm_current_desc = current_desc or None

                if norm_version != norm_current_version or norm_desc != norm_current_desc:
                    to_update.append((name, version, desc))

        to_remove = [name for name in current_modules if name not in found_module_names]

        return to_update, to_remove, modules_yml_path

    def update_modules_yml(self, path: Path, to_update: List[Tuple[str, Optional[str], Optional[str]]], to_remove: List[str]):
        """更新 modules.yml，保持原有顺序并更新元数据。"""
        current = self._read_modules_yml(path)

        # 删除不存在的模块
        for name in to_remove:
            if name in current:
                del current[name]

        # 更新现有模块的元数据（保持原有顺序）
        for name, version, desc in to_update:
            if name in current:
                # 更新已有模块的元数据
                if version:
                    current[name]["version"] = version
                if desc:
                    current[name]["description"] = desc
            else:
                # 添加新模块（在末尾）
                info = {}
                if version:
                    info["version"] = version
                if desc:
                    info["description"] = desc
                current[name] = info

        self._write_modules_yml(path, current)
