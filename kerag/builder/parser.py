"""Parser for converting tokens to blocks using finite state machine."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from kerag.builder.tokenizer import Token


class BlockType(Enum):
    """Types of blocks."""
    HEADER = "header"
    CONTENT = "content"
    SUBTREE_REF = "subtree_ref"
    SEE_ALSO = "see_also"
    SECTION_FENCE = "section_fence"
    BLANK = "blank"


@dataclass
class Block:
    """A block of tokens representing a logical unit.

    Attributes:
        type: Type of block
        tokens: List of tokens in this block
        metadata: Additional metadata about the block
    """
    type: BlockType
    tokens: List[Token] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BlockInfo:
    """Information about a block."""
    block_id: str
    start_line: int
    end_line: int
    level: Optional[int] = None
    label: Optional[str] = None


class ParserState(Enum):
    """States in the finite state machine."""
    DEFAULT = "default"
    HEADER_BLOCK = "header_block"
    CONTENT_BLOCK = "content_block"
    SUBTREE_REF_BLOCK = "subtree_ref_block"
    SEE_ALSO_BLOCK = "see_also_block"
    SECTION_FENCE_BLOCK = "section_fence_block"


class Parser:
    """Parser that converts tokens to blocks using FSA."""

    def __init__(self):
        """Initialize the parser."""
        self.state = ParserState.DEFAULT
        self.current_block: Optional[Block] = None
        self.blocks: List[Block] = []

    def reset(self):
        """Reset parser to initial state."""
        self.state = ParserState.DEFAULT
        self.current_block = None
        self.blocks = []

    def parse_tokens(self, tokens: List[Token]) -> List[Block]:
        """Parse a list of tokens into blocks.

        Args:
            tokens: List of tokens to parse

        Returns:
            List of blocks
        """
        self.reset()

        for token in tokens:
            self._process_token(token)

        # Finish any remaining block
        self._finish_current_block()

        return self.blocks

    def _process_token(self, token: Token):
        """Process a single token based on current state.

        Args:
            token: Token to process
        """
        if self.state == ParserState.DEFAULT:
            self._process_in_default(token)
        elif self.state == ParserState.HEADER_BLOCK:
            self._process_in_header_block(token)
        elif self.state == ParserState.CONTENT_BLOCK:
            self._process_in_content_block(token)
        elif self.state == ParserState.SUBTREE_REF_BLOCK:
            self._process_in_subtree_ref_block(token)
        elif self.state == ParserState.SEE_ALSO_BLOCK:
            self._process_in_see_also_block(token)
        elif self.state == ParserState.SECTION_FENCE_BLOCK:
            self._process_in_section_fence_block(token)

    def _process_in_default(self, token: Token):
        """Process token when in DEFAULT state.

        Args:
            token: Token to process
        """
        if token.type == 'header':
            self._finish_current_block()
            self._start_new_block(BlockType.HEADER, token)
            self.state = ParserState.HEADER_BLOCK

        elif token.type == 'see_also_header':
            self._finish_current_block()
            self._start_new_block(BlockType.SEE_ALSO, token)
            self.state = ParserState.SEE_ALSO_BLOCK

        elif token.type == 'subtree_ref_header':
            self._finish_current_block()
            self._start_new_block(BlockType.SUBTREE_REF, token)
            self.state = ParserState.SUBTREE_REF_BLOCK

        elif token.type == 'section_fence':
            self._finish_current_block()
            self._start_new_block(BlockType.SECTION_FENCE, token)
            self.state = ParserState.SECTION_FENCE_BLOCK

        elif token.type == 'content':
            self._finish_current_block()
            self._start_new_block(BlockType.CONTENT, token)
            self.state = ParserState.CONTENT_BLOCK

        elif token.type == 'blank':
            # In DEFAULT state, blank lines are ignored
            pass

    def _process_in_header_block(self, token: Token):
        """Process token when in HEADER_BLOCK state.

        Args:
            token: Token to process
        """
        if token.type == 'header':
            self._finish_current_block()
            self._start_new_block(BlockType.HEADER, token)
            # Stay in HEADER_BLOCK state

        elif token.type == 'see_also_header':
            self._finish_current_block()
            self._start_new_block(BlockType.SEE_ALSO, token)
            self.state = ParserState.SEE_ALSO_BLOCK

        elif token.type == 'subtree_ref_header':
            self._finish_current_block()
            self._start_new_block(BlockType.SUBTREE_REF, token)
            self.state = ParserState.SUBTREE_REF_BLOCK

        elif token.type == 'section_fence':
            self._finish_current_block()
            self._start_new_block(BlockType.SECTION_FENCE, token)
            self.state = ParserState.SECTION_FENCE_BLOCK

        elif token.type == 'content':
            self._finish_current_block()
            self._start_new_block(BlockType.CONTENT, token)
            self.state = ParserState.CONTENT_BLOCK

        elif token.type == 'blank':
            self._finish_current_block()
            self.state = ParserState.DEFAULT

    def _process_in_content_block(self, token: Token):
        """Process token when in CONTENT_BLOCK state.

        Args:
            token: Token to process
        """
        if token.type == 'content':
            # Continue accumulating content
            if self.current_block:
                self.current_block.tokens.append(token)

        elif token.type == 'blank':
            # Blank line separates content blocks
            self._finish_current_block()
            self.state = ParserState.DEFAULT

        else:
            # Different token type, finish content block and start new
            self._finish_current_block()
            self._process_in_default(token)

    def _process_in_subtree_ref_block(self, token: Token):
        """Process token when in SUBTREE_REF_BLOCK state.

        Args:
            token: Token to process
        """
        if token.type == 'subtree_ref_header':
            self._finish_current_block()
            self._start_new_block(BlockType.SUBTREE_REF, token)
            # Stay in SUBTREE_REF_BLOCK state

        elif token.type == 'blank':
            self._finish_current_block()
            self.state = ParserState.DEFAULT

        else:
            # Different token type
            self._finish_current_block()
            self._process_in_default(token)

    def _process_in_see_also_block(self, token: Token):
        """Process token when in SEE_ALSO_BLOCK state.

        Args:
            token: Token to process
        """
        if token.type == 'see_also_header':
            # Start a new see-also block
            self._finish_current_block()
            self._start_new_block(BlockType.SEE_ALSO, token)
            # Stay in SEE_ALSO_BLOCK state

        elif token.type == 'see_also_item':
            # Add see-also item to current block
            if self.current_block:
                self.current_block.tokens.append(token)
            else:
                # No current block, start one
                self._start_new_block(BlockType.SEE_ALSO, token)

        elif token.type == 'blank':
            # Blank line separates see-also items, but stay in SEE_ALSO_BLOCK state
            if self.current_block:
                self.current_block.tokens.append(token)

        else:
            # Different token type, finish current block and start new one
            self._finish_current_block()
            self._process_in_default(token)

    def _process_in_section_fence_block(self, token: Token):
        """Process token when in SECTION_FENCE_BLOCK state.

        Args:
            token: Token to process
        """
        if token.type == 'section_fence':
            self._finish_current_block()
            self._start_new_block(BlockType.SECTION_FENCE, token)
            # Stay in SECTION_FENCE_BLOCK state

        elif token.type == 'blank':
            self._finish_current_block()
            self.state = ParserState.DEFAULT

        else:
            # Different token type
            self._finish_current_block()
            self._process_in_default(token)

    def _start_new_block(self, block_type: BlockType, token: Token):
        """Start a new block with the given token.

        Args:
            block_type: Type of block to start
            token: First token in the block
        """
        self.current_block = Block(
            type=block_type,
            tokens=[token],
            metadata={
                'start_line': token.line_number,
                'end_line': token.line_number,
                'token_types': [token.type]
            }
        )

    def _finish_current_block(self):
        """Finish the current block and add it to the list."""
        if self.current_block:
            # Update end line in metadata
            if self.current_block.tokens:
                last_token = self.current_block.tokens[-1]
                self.current_block.metadata['end_line'] = last_token.line_number

            # Add block info
            first_token = self.current_block.tokens[0]

            # Determine label based on block type
            if self.current_block.type == BlockType.CONTENT:
                # For content blocks, label is in the last token's content_label
                label = last_token.metadata.get('content_label')
            else:
                # For header and other blocks, label is in the first token
                label = first_token.metadata.get('label')

            block_info = BlockInfo(
                block_id=f"block_{len(self.blocks)}",
                start_line=first_token.line_number,
                end_line=self.current_block.metadata['end_line'],
                level=first_token.metadata.get('level'),
                label=label
            )
            self.current_block.metadata['info'] = block_info

            self.blocks.append(self.current_block)
            self.current_block = None

    @staticmethod
    def parse(tokens: List[Token]) -> List[Block]:
        """Static method to parse tokens into blocks.

        Args:
            tokens: List of tokens

        Returns:
            List of blocks
        """
        parser = Parser()
        return parser.parse_tokens(tokens)