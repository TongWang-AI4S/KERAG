"""
模块元数据解析功能
"""
from pathlib import Path
from typing import Tuple, Optional, Dict


def parse_modules_txt_line(line: str) -> Tuple[str, Optional[str]]:
    """
    解析 modules.txt 的一行，支持 name=version 格式（允许等号两侧有空格）

    示例:
        "module1=v1.0" -> ("module1", "v1.0")
        "module2 = v2.0" -> ("module2", "v2.0")
        "module3" -> ("module3", None)
        "module4 = v4.0" -> ("module4", "v4.0")

    返回:
        Tuple[str, Optional[str]]: (模块名称, 版本) 或 (模块名称, None)
    """
    line = line.strip()
    if not line:
        return None

    if '=' in line:
        name, version = line.split('=', 1)
        return name.strip(), version.strip()  # strip()处理等号两侧的空格
    else:
        return line.strip(), None


def extract_from_kerag_meta(meta_path: Path) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    从 kerag_meta.txt 提取模块名称、版本和描述

    kerag_meta.txt 格式:
        test-module=v1.0.0
        Description: 这是一个测试模块

    返回:
        Tuple[Optional[str], Optional[str], Optional[str]]: (名称, 版本, 描述)
    """
    if not meta_path.exists():
        return None, None, None

    lines = meta_path.read_text().strip().split('\n')
    if not lines:
        return None, None, None

    name = None
    version = None
    description = None

    # 第一行可能包含 name=version
    first_line = lines[0].strip()
    if '=' in first_line:
        name_part, version_part = first_line.split('=', 1)
        name = name_part.strip()
        version = version_part.strip()

    # 查找 Description: 行
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith('description:'):
            description = stripped[len('description:'):].strip()
            break

    return name, version, description


def extract_from_index_md(index_path: Path) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    从 index.md 的注释中提取模块名称、版本和描述
    仅匹配 <!-- Module: -->、<!-- Version: --> 和 <!-- Description: --> 单行格式

    返回:
        Tuple[Optional[str], Optional[str], Optional[str]]: (名称, 版本, 描述)
    """
    if not index_path.exists():
        return None, None, None

    content = index_path.read_text()
    lines = content.split('\n')

    module_name = None
    version = None
    description = None

    for line in lines[:10]:  # 只检查前10行
        stripped = line.strip()

        # 匹配 <!-- Module: name --> 格式
        if stripped.startswith('<!-- Module:') and stripped.endswith('-->'):
            try:
                module_name = stripped.split('Module:', 1)[1].rsplit('-->', 1)[0].strip()
            except (IndexError, ValueError):
                pass

        # 匹配 <!-- Version: version --> 格式（使用独立的if，允许没有Module但有Version）
        if stripped.startswith('<!-- Version:') and stripped.endswith('-->'):
            try:
                version = stripped.split('Version:', 1)[1].rsplit('-->', 1)[0].strip()
            except (IndexError, ValueError):
                pass

        # 匹配 <!-- Description: description --> 格式（使用独立的if，允许没有Module但有Description）
        if stripped.startswith('<!-- Description:') and stripped.endswith('-->'):
            try:
                description = stripped.split('Description:', 1)[1].rsplit('-->', 1)[0].strip()
            except (IndexError, ValueError):
                pass

    return module_name, version, description


def generate_module_entry(name: str, version: Optional[str]) -> str:
    """
    生成 modules.txt 条目格式

    参数:
        name: 模块名称
        version: 版本字符串或 None

    返回:
        str: modules.txt 行格式
    """
    if version:
        return f"{name}={version}"
    else:
        return name
