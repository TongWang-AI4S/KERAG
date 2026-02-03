"""Tokenizer for parsing markdown documents into tokens."""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple


@dataclass
class Token:
    """Token representing a line in a markdown document.

    Attributes:
        line_number: Line number in the source file (1-indexed)
        content: Raw content of the line
        type: Type of token (header, see_also, subtree_ref, content, etc.)
        metadata: Additional metadata specific to token type
    """
    line_number: int
    content: str
    type: str
    metadata: Dict[str, any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Tokenizer:
    """Tokenizer for markdown documents with special KERAG syntax."""

    # Reference pattern for subtree references: (@node_id)
    REF_PATTERN = re.compile(r'\(@([^)]+)\)')

    # SeeAlso pattern: (@node_id) or (@node_id):description
    SEE_ALSO_PATTERN = re.compile(r'^\(@([^)]+)\)(?::(.*))?$')

    # Label pattern: (optional space)[@label]
    LABEL_PATTERN = re.compile(r'(?:[^\S\r\n]*)\[@([^]]+)\]')

    # Comment pattern: <!-- ... -->
    COMMENT_PATTERN = re.compile(r'^\s*<!--.*?-->\s*$')

    # Code fence start: ```[lang]
    CODE_FENCE_START = re.compile(r'^\s*```\s*([^\s]+(?: [^\s]+)*)\s*$')

    # Code fence end: ```
    CODE_FENCE_END = re.compile(r'^\s*```\s*$')

    # Header pattern: #+ space + ...
    HEADER_PATTERN = re.compile(r'^(\s*)(#+)\s+(.*)$')

    # Section fence: at least 4 *'s
    SECTION_FENCE_PATTERN = re.compile(r'^\s*\*{4,}\s*$')

    # Blank line: only whitespace
    BLANK_PATTERN = re.compile(r'^\s*$')

    # See also titles (case-insensitive)
    SEE_ALSO_TITLES = [
        'see also',
        '参见',
    ]

    def __init__(self):
        """Initialize the tokenizer."""
        self._in_code_fence = False
        self._current_file_path = None

    def tokenize_file(self, file_path: str) -> List[Token]:
        """Tokenize an entire file.

        Args:
            file_path: Path to the markdown file

        Returns:
            List of Token objects
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        return self.tokenize_lines(lines, file_path)

    def tokenize_lines(self, lines: List[str], file_path: Optional[str] = None) -> List[Token]:
        """Tokenize a list of lines.

        Args:
            lines: List of strings, each representing a line
            file_path: Optional path for reference

        Returns:
            List of Token objects
        """
        self._in_code_fence = False
        self._current_file_path = file_path

        tokens = []
        for line_num, line in enumerate(lines, 1):
            token = self._tokenize_line(line.rstrip('\n\r'), line_num)
            if token:  # None means skip (comment line)
                tokens.append(token)

        return tokens

    def _tokenize_line(self, line: str, line_number: int) -> Optional[Token]:
        """Tokenize a single line.

        Args:
            line: The line content
            line_number: Line number (1-indexed)

        Returns:
            Token object or None if line should be skipped (comments)
        """
        # Skip comment lines
        if self.COMMENT_PATTERN.match(line):
            return None

        # Handle code fence state
        if self._in_code_fence:
            # Check if this line ends the code fence
            if self.CODE_FENCE_END.match(line):
                self._in_code_fence = False
            # Everything in code fence is content
            return Token(line_number, line, 'content', {})
        else:
            # Check if this line starts a code fence
            if self.CODE_FENCE_START.match(line):
                self._in_code_fence = True
                return Token(line_number, line, 'content', {})

        # Check for blank lines
        if self.BLANK_PATTERN.match(line):
            return Token(line_number, line, 'blank', {})

        # Check for section fences
        if self.SECTION_FENCE_PATTERN.match(line):
            return Token(line_number, line, 'section_fence', {})

        # Check for see-also reference format: (@node_id) or (@node_id):description
        see_also_match = self.SEE_ALSO_PATTERN.match(line.strip())
        if see_also_match:
            ref_id = see_also_match.group(1)
            description = see_also_match.group(2) or ''
            metadata = {
                'reference_id': ref_id,
                'description': description.strip()
            }
            return Token(line_number, line, 'see_also_item', metadata)

        # Check for headers
        header_match = self.HEADER_PATTERN.match(line)
        if header_match:
            indent, hashes, content = header_match.groups()
            level = len(hashes)

            # Extract label if present
            label = self._extract_label(content)
            if label:
                # Remove label from content
                content = content.replace(f'[@{label}]', '').strip()

            metadata = {
                'level': level,
                'title': content,
                'indent': len(indent),
                'label': label
            }

            # Check if it's a see-also header
            if self._is_see_also_title(content):
                return Token(line_number, line, 'see_also_header', metadata)

            # Check if it's a subtree reference header
            ref_id = self._extract_reference(content)
            if ref_id:
                metadata['reference_id'] = ref_id
                return Token(line_number, line, 'subtree_ref_header', metadata)

            # Regular header
            return Token(line_number, line, 'header', metadata)

        # Default: content line
        metadata = {
            'inline_links': self._extract_all_references(line)
        }
        # Also extract content label if present
        content_label = self._extract_label(line)
        if content_label:
            metadata['content_label'] = content_label
        return Token(line_number, line, 'content', metadata)

    def _extract_label(self, line: str) -> Optional[str]:
        """Extract label from a line.

        Args:
            line: The line to extract label from

        Returns:
            Label string or None if not found
        """
        match = self.LABEL_PATTERN.search(line)
        if match:
            return match.group(1)
        return None

    def _extract_reference(self, line: str) -> Optional[str]:
        """Extract subtree reference ID from a line.

        Args:
            line: The line to extract reference from

        Returns:
            Reference ID or None if not found
        """
        match = self.REF_PATTERN.search(line)
        if match:
            return match.group(1)
        return None

    def _extract_all_references(self, line: str) -> List[str]:
        """Extract all subtree reference IDs from a line.

        Args:
            line: The line to extract references from

        Returns:
            List of reference IDs
        """
        return [match.group(1) for match in self.REF_PATTERN.finditer(line)]

    def _is_see_also_title(self, title: str) -> bool:
        """Check if a title is a "see also" title.

        Args:
            title: The title text to check

        Returns:
            True if it's a see-also title
        """
        title_lower = title.strip().lower()
        return any(see_also.lower() == title_lower for see_also in self.SEE_ALSO_TITLES)


def tokenize_file(file_path: str) -> List[Token]:
    """Convenience function to tokenize a file.

    Args:
        file_path: Path to the markdown file

    Returns:
        List of Token objects
    """
    tokenizer = Tokenizer()
    return tokenizer.tokenize_file(file_path)


def tokenize_lines(lines: List[str], file_path: Optional[str] = None) -> List[Token]:
    """Convenience function to tokenize lines.

    Args:
        lines: List of strings representing lines
        file_path: Optional path for reference

    Returns:
        List of Token objects
    """
    tokenizer = Tokenizer()
    return tokenizer.tokenize_lines(lines, file_path)
