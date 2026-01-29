#!/usr/bin/env python3
"""
Markdown文档分割工具

将大型Markdown文档按指定层级分割为多个子文档，使用子树引用连接
"""

import re
import sys
from pathlib import Path
from typing import List, Optional
import argparse


def sanitize_title(title: str) -> str:
    """将标题转换为文件友好的名称

    替换空格和特殊字符为连字符，保留中文和其他Unicode字符
    返回小写版本，移除开头和结尾的连字符，并将连续的连字符替换为单个连字符
    """
    # 将空格和特殊字符替换为连字符
    sanitized = re.sub(r'[\s!@#$%^&*()+=\[\]{};:"\\|,.<>\/?]+', '-', title.lower())
    # 将连续的连字符替换为单个连字符
    sanitized = re.sub(r'-+', '-', sanitized)
    # 移除开头和结尾的连字符
    sanitized = sanitized.strip('-')
    # 限制长度
    return sanitized[:100] if sanitized else 'untitled'


def split_markdown(file_path: Path, split_level: int, output_dir: Path, all_labeled: bool = False) -> dict:
    """分割Markdown文档

    Args:
        file_path: 输入的Markdown文件路径
        split_level: 分割层级（如3表示###级别）
        output_dir: 输出目录
        all_labeled: 是否为所有标题添加[@label]标签

    Returns:
        分割结果统计信息
    """
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # 读取原始文件
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 状态变量
    state = 'main'  # 'main' 或 'sub'
    within_fence = False  # 是否在代码块中
    main_lines: List[str] = []
    sub_lines: List[str] = []
    current_sub_title = ""
    sub_files = []
    line_num = 0

    title_pattern = re.compile(r'^(#+)\s+(.+)$')

    # 遍历每一行
    for line in lines:
        line_num += 1

        # 检查是否进入或离开代码块
        stripped_line = line.strip()
        if stripped_line.startswith('```'):
            within_fence = not within_fence

        # 只有在非代码块中才匹配标题
        match = None
        if not within_fence:
            match = title_pattern.match(line)

        if state == 'main':
            if not match:
                # 普通行，直接添加到主文档
                main_lines.append(line)
            else:
                hashes, title = match.group(1), match.group(2)
                level = len(hashes)

                if level < split_level:
                    # 更低层级的标题，保留在主文档
                    if all_labeled:
                        sanitized = sanitize_title(title)
                        labeled_line = f"{hashes} {title} [@{sanitized}]\n"
                        main_lines.append(labeled_line)
                    else:
                        main_lines.append(line)
                elif level == split_level:
                    # 目标层级的标题，切换到子文档模式
                    state = 'sub'

                    # 生成子文档名称
                    sanitized = sanitize_title(title)
                    current_sub_title = sanitized

                    # 在主文档中添加子树引用（额外添加空行）
                    ref_line = f"{hashes} (@{sanitized}::{sanitized})\n\n"
                    main_lines.append(ref_line)

                    # 开始新的子文档
                    sub_lines = [f"# {title} [@{sanitized}]\n"]
                else:
                    # 更高层级的标题（不应该发生）
                    main_lines.append(line)

        else:  # state == 'sub'
            if not match:
                # 普通行，添加到子文档
                sub_lines.append(line)
            else:
                hashes, title = match.group(1), match.group(2)
                level = len(hashes)

                if level < split_level:
                    # 遇到更低层级的标题，返回主文档模式
                    state = 'main'

                    # 刷新当前子文档
                    if current_sub_title and sub_lines:
                        sub_file = output_dir / f"{current_sub_title}.md"
                        with open(sub_file, 'w', encoding='utf-8') as f:
                            f.writelines(sub_lines)
                        sub_files.append({
                            'file': sub_file,
                            'title': current_sub_title,
                            'lines': len(sub_lines)
                        })

                    # 重置子文档
                    sub_lines = []
                    current_sub_title = ""

                    # 这行添加到主文档
                    main_lines.append(line)

                elif level == split_level:
                    # 新的同级标题
                    # 刷新前一个子文档
                    if current_sub_title and sub_lines:
                        sub_file = output_dir / f"{current_sub_title}.md"
                        with open(sub_file, 'w', encoding='utf-8') as f:
                            f.writelines(sub_lines)
                        sub_files.append({
                            'file': sub_file,
                            'title': current_sub_title,
                            'lines': len(sub_lines)
                        })

                    # 开始新的子文档
                    sanitized = sanitize_title(title)
                    current_sub_title = sanitized

                    # 在主文档中添加子树引用（额外添加空行）
                    ref_line = f"{hashes} (@{sanitized}::{sanitized})\n\n"
                    main_lines.append(ref_line)

                    # 新的子文档内容，标题使用引用格式
                    sub_lines = [f"# {title} [@{sanitized}]\n"]

                else:  # level > split_level
                    # 更高层级的标题（在子文档中）
                    # 调整标题层级：移除 (split_level - 1) 个 "#"
                    adjusted_level = level - (split_level - 1)
                    adjusted_hashes = '#' * adjusted_level
                    if all_labeled:
                        sanitized = sanitize_title(title)
                        adjusted_line = f"{adjusted_hashes} {title} [@{sanitized}]\n"
                    else:
                        adjusted_line = f"{adjusted_hashes} {title}\n"
                    sub_lines.append(adjusted_line)

    # 循环结束，处理剩余内容
    if state == 'sub' and current_sub_title and sub_lines:
        # 刷新最后一个子文档
        sub_file = output_dir / f"{current_sub_title}.md"
        with open(sub_file, 'w', encoding='utf-8') as f:
            f.writelines(sub_lines)
        sub_files.append({
            'file': sub_file,
            'title': current_sub_title,
            'lines': len(sub_lines)
        })

    # 写入主文档
    main_file = output_dir / "index.md"
    with open(main_file, 'w', encoding='utf-8') as f:
        f.writelines(main_lines)

    return {
        'main_file': str(main_file),
        'sub_files': sub_files,
        'total_sub_files': len(sub_files),
        'total_lines_processed': line_num
    }


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='将大型Markdown文档按指定层级分割'
    )
    parser.add_argument('file', help='输入的Markdown文件')
    parser.add_argument('-o', '--output', default='output',
                       help='输出目录（默认：output）')
    parser.add_argument('-l', '--level', type=int, default=3,
                       help='分割层级（默认：3，表示从###开始分割）')

    args = parser.parse_args()

    file_path = Path(args.file)
    output_dir = Path(args.output)
    split_level = args.level

    if split_level < 1 or split_level > 6:
        print(f"错误：分割层级必须在1-6之间，当前：{split_level}", file=sys.stderr)
        sys.exit(1)

    try:
        result = split_markdown(file_path, split_level, output_dir)

        print(f"✓ 文档分割完成")
        print(f"  - 主文件： {result['main_file']}")
        print(f"  - 子文件数： {result['total_sub_files']}")
        print(f"  - 总行数： {result['total_lines_processed']}")
        print(f"\n生成的子文件：")
        for sub in result['sub_files']:
            print(f"  - {sub['file']} ({sub['lines']} 行)")

    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
