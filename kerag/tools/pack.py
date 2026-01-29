#!/usr/bin/env python3
"""
KERAG Module Packager

Pack knowledge modules into distributable tar files with metadata support.
"""

import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

from kerag.modules.metadata import extract_from_kerag_meta, extract_from_index_md


class Packager:
    """Packager for KERAG knowledge modules."""

    def __init__(self, module_dir: Path, meta_file: Optional[Path] = None,
                 name: Optional[str] = None, version: Optional[str] = None,
                 description: Optional[str] = None, output_path: Optional[str] = None):
        """
        Initialize packager.

        Args:
            module_dir: Module directory to pack
            meta_file: Optional kerag_meta.txt file path
            name: Module name (overrides detected name)
            version: Module version (overrides detected version)
            description: Module description (overrides detected description)
            output_path: Optional specific output filename or path
        """
        self.module_dir = Path(module_dir).resolve()
        self.meta_file = Path(meta_file).resolve() if meta_file else None
        self.name = name
        self.version = version
        self.description = description
        self.output_path = output_path

        if not self.module_dir.is_dir():
            raise ValueError(f"Module directory not found: {self.module_dir}")

    def pack(self) -> Tuple[bool, str]:
        """
        Pack the module into a tar file.

        Returns:
            Tuple[bool, str]: (success, message or output file path)
        """
        try:
            # 1. Extract metadata from all sources
            metadata = self._extract_metadata()

            # 2. Generate kerag_meta.txt content
            kerag_meta_content = self._generate_kerag_meta(metadata)

            # 3. Create temporary directory structure
            temp_dir = self._create_temp_structure(kerag_meta_content)

            # 4. Create tar file
            output_file = self._create_tar(temp_dir, metadata)

            # 5. Clean up
            shutil.rmtree(temp_dir)

            return True, str(output_file)

        except Exception as e:
            return False, f"Packaging failed: {str(e)}"

    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract and merge metadata from all sources."""
        # Step 1: Extract from each source
        sources = {}

        # From meta file (only if explicitly provided)
        if self.meta_file:
            if not self.meta_file.exists():
                raise ValueError(f"Specified meta file not found: {self.meta_file}")
            meta_name, meta_version, meta_desc = extract_from_kerag_meta(self.meta_file)
            sources['meta_file'] = {
                'name': meta_name,
                'version': meta_version,
                'description': meta_desc,
                'path': str(self.meta_file)
            }

        # From index.md
        index_path = self.module_dir / "index.md"
        if index_path.exists():
            index_name, index_version, index_desc = extract_from_index_md(index_path)
            sources['index'] = {
                'name': index_name,
                'version': index_version,
                'description': index_desc,
                'path': str(index_path)
            }

        # From command line
        if self.name or self.version or self.description:
            sources['command_line'] = {
                'name': self.name,
                'version': self.version,
                'description': self.description,
                'path': 'command line arguments'
            }

        # Step 2: Check for conflicts between ALL sources
        def normalize(value):
            return None if value is None or value == "" else value

        conflicts = []
        sources_to_check = list(sources.keys())

        # Check all pairs of sources for conflicts
        for i, source1 in enumerate(sources_to_check):
            for source2 in sources_to_check[i + 1:]:
                # Check name conflict
                val1 = normalize(sources[source1]['name'])
                val2 = normalize(sources[source2]['name'])
                if val1 and val2 and val1 != val2:
                    conflicts.append(
                        f"name conflict: {source1} ('{val1}') vs {source2} ('{val2}')"
                    )

                # Check version conflict
                val1 = normalize(sources[source1]['version'])
                val2 = normalize(sources[source2]['version'])
                if val1 and val2 and val1 != val2:
                    conflicts.append(
                        f"version conflict: {source1} ('{val1}') vs {source2} ('{val2}')"
                    )

                # Check description conflict
                val1 = normalize(sources[source1]['description'])
                val2 = normalize(sources[source2]['description'])
                if val1 and val2 and val1 != val2:
                    conflicts.append(
                        f"description conflict: {source1} ('{val1}') vs {source2} ('{val2}')"
                    )

        if conflicts:
            conflict_details = "\n  ".join(conflicts)
            raise ValueError(
                f"Metadata conflicts detected between sources:\n  {conflict_details}\n\n"
                f"All provided metadata sources (index.md, meta file, command line) must be consistent."
            )

        # Step 3: Merge metadata (since they are consistent, priority only matters for missing values)
        final_metadata = {
            'name': None,
            'version': None,
            'description': None
        }

        # Combine results (any source will have the same value due to check above)
        for source in ['index', 'meta_file', 'command_line']:
            if source in sources:
                for key in ['name', 'version', 'description']:
                    val = normalize(sources[source][key])
                    if val:
                        final_metadata[key] = val

        # Final fallback: use directory name if no name provided anywhere
        if not final_metadata['name']:
            final_metadata['name'] = self.module_dir.name

        return final_metadata

    def _generate_kerag_meta(self, metadata: Dict[str, Any]) -> str:
        """Generate kerag_meta.txt content."""
        lines = []

        # First line: name=version
        name = metadata.get("name", self.module_dir.name)
        version = metadata.get("version")
        if version:
            lines.append(f"{name}={version}")
        else:
            lines.append(name)

        # Second line: directory name
        lines.append(self.module_dir.name)

        # Third line: description (if available)
        description = metadata.get("description")
        if description:
            lines.append(f"Description: {description}")

        return "\n".join(lines)

    def _create_temp_structure(self, kerag_meta_content: str) -> Path:
        """Create temporary directory structure for packaging."""
        temp_dir = Path(tempfile.mkdtemp())

        # Write kerag_meta.txt directly in temp_dir
        kerag_meta_path = temp_dir / "kerag_meta.txt"
        kerag_meta_path.write_text(kerag_meta_content, encoding="utf-8")

        # Copy module directory into temp_dir
        module_name = self.module_dir.name
        module_dest = temp_dir / module_name
        shutil.copytree(self.module_dir, module_dest)

        return temp_dir

    def _create_tar(self, temp_dir: Path, metadata: Dict[str, Any]) -> Path:
        """Create tar file from temporary directory."""
        if self.output_path:
            output_path = Path(self.output_path).resolve()
        else:
            module_name = metadata.get("name", self.module_dir.name)
            version = metadata.get("version")

            # Generate output filename
            if version:
                tar_name = f"{module_name}-{version}.tar"
            else:
                tar_name = f"{module_name}.tar"

            # Create tar file in current directory
            output_path = Path.cwd() / tar_name

        # Create tar file adding contents of temp_dir
        with tarfile.open(output_path, "w") as tar:
            for item in temp_dir.iterdir():
                tar.add(item, arcname=item.name)

        return output_path


def pack_module(module_dir: str, meta_file: Optional[str] = None,
                name: Optional[str] = None, version: Optional[str] = None,
                description: Optional[str] = None, output_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Pack a knowledge module.

    Args:
        module_dir: Module directory path
        meta_file: Optional kerag_meta.txt file path
        name: Module name (overrides detected name)
        version: Module version (overrides detected version)
        description: Module description (overrides detected description)
        output_path: Optional specific output filename or path

    Returns:
        Tuple[bool, str]: (success, message or output file path)
    """
    try:
        packager = Packager(
            module_dir=Path(module_dir),
            meta_file=Path(meta_file) if meta_file else None,
            name=name,
            version=version,
            description=description,
            output_path=output_path
        )
        return packager.pack()
    except Exception as e:
        return False, f"Error: {str(e)}"
