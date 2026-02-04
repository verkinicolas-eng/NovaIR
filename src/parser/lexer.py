"""
NovaIR Lexer - Tokenizes NovaIR source code.

This module breaks down the source text into tokens that the parser can process.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


class TokenType(Enum):
    """Token types for NovaIR."""
    # Keywords
    SYSTEM = auto()
    STATE = auto()
    CONSTRAINTS = auto()
    OBJECTIVES = auto()
    ACTIONS = auto()
    TICK = auto()
    PARAMETERS = auto()
    EFFECTS = auto()
    COST = auto()
    TARGET = auto()
    MIN = auto()
    MAX = auto()
    TO = auto()
    INTERVAL = auto()
    ACTION_THRESHOLD = auto()
    MODE = auto()

    # Annotations
    VERSION = auto()
    CRITICAL = auto()
    WARNING = auto()
    PRIORITY = auto()

    # Cost levels
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()

    # Tick modes
    CONTINUOUS = auto()
    REACTIVE = auto()

    # Operators
    ARROW_LEFT = auto()   # <-
    ARROW_RIGHT = auto()  # ->
    COLON = auto()        # :
    COMMA = auto()        # ,
    DOT = auto()          # .
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    LBRACKET = auto()     # [
    RBRACKET = auto()     # ]
    RANGE = auto()        # ..

    # Comparison operators
    LTE = auto()          # <=
    GTE = auto()          # >=
    LT = auto()           # <
    GT = auto()           # >
    EQ = auto()           # ==
    NEQ = auto()          # !=

    # Values
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    UNIT = auto()

    # Structure
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()

    # Special
    COMMENT = auto()


@dataclass
class Token:
    """A token with type, value, and position information."""
    type: TokenType
    value: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"Token({self.type.name}, {repr(self.value)}, line={self.line})"


class LexerError(Exception):
    """Error during lexical analysis."""
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, column {column}: {message}")


class Lexer:
    """Tokenizes NovaIR source code."""

    # Keywords mapping
    KEYWORDS = {
        "system": TokenType.SYSTEM,
        "state": TokenType.STATE,
        "constraints": TokenType.CONSTRAINTS,
        "objectives": TokenType.OBJECTIVES,
        "actions": TokenType.ACTIONS,
        "tick": TokenType.TICK,
        "parameters": TokenType.PARAMETERS,
        "effects": TokenType.EFFECTS,
        "cost": TokenType.COST,
        "target": TokenType.TARGET,
        "min": TokenType.MIN,
        "max": TokenType.MAX,
        "to": TokenType.TO,
        "interval": TokenType.INTERVAL,
        "action_threshold": TokenType.ACTION_THRESHOLD,
        "mode": TokenType.MODE,
        "low": TokenType.LOW,
        "medium": TokenType.MEDIUM,
        "high": TokenType.HIGH,
        "continuous": TokenType.CONTINUOUS,
        "reactive": TokenType.REACTIVE,
    }

    # Common units
    UNITS = {
        "°C", "°F", "K",           # Temperature
        "%",                        # Percentage
        "B", "KB", "MB", "GB", "TB", # Data
        "ms", "s", "m", "h",        # Time
        "Hz", "kHz", "MHz", "GHz",  # Frequency
        "W", "kW", "mW",            # Power
        "dB", "dBA",                # Sound
    }

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.indent_stack = [0]

    def tokenize(self) -> List[Token]:
        """Tokenize the entire source and return a list of tokens."""
        self.tokens = []
        self.indent_stack = [0]

        while self.pos < len(self.source):
            # Handle line start (indentation)
            if self.column == 1:
                self._handle_indentation()

            # Skip whitespace (but not newlines)
            if self._peek() in " \t" and self.column > 1:
                self._advance()
                continue

            # Handle newlines
            if self._peek() == "\n":
                self._add_token(TokenType.NEWLINE, "\n")
                self._advance()
                self.line += 1
                self.column = 1
                continue

            # Handle comments
            if self._peek() == "#":
                self._skip_comment()
                continue

            # Handle operators and punctuation
            if self._match_operator():
                continue

            # Handle strings
            if self._peek() == '"':
                self._read_string()
                continue

            # Handle numbers (including negative and with units)
            if self._peek().isdigit() or (self._peek() in "+-" and self._peek_ahead().isdigit()):
                self._read_number()
                continue

            # Handle identifiers and keywords
            if self._peek().isalpha() or self._peek() == "_":
                self._read_identifier()
                continue

            # Handle annotations
            if self._peek() == "@":
                self._read_annotation()
                continue

            raise LexerError(f"Unexpected character: {self._peek()}", self.line, self.column)

        # Handle remaining dedents
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self._add_token(TokenType.DEDENT, "")

        self._add_token(TokenType.EOF, "")
        return self.tokens

    def _peek(self) -> str:
        """Return current character without advancing."""
        if self.pos >= len(self.source):
            return "\0"
        return self.source[self.pos]

    def _peek_ahead(self, offset: int = 1) -> str:
        """Return character at offset from current position."""
        pos = self.pos + offset
        if pos >= len(self.source):
            return "\0"
        return self.source[pos]

    def _advance(self) -> str:
        """Consume and return current character."""
        char = self._peek()
        self.pos += 1
        self.column += 1
        return char

    def _add_token(self, type: TokenType, value: str):
        """Add a token to the list."""
        token = Token(type, value, self.line, self.column - len(value))
        self.tokens.append(token)

    def _handle_indentation(self):
        """Handle indentation at the start of a line."""
        indent = 0
        while self._peek() == " ":
            self._advance()
            indent += 1

        # Skip empty lines
        if self._peek() in "\n\0#":
            return

        current_indent = self.indent_stack[-1]

        if indent > current_indent:
            self.indent_stack.append(indent)
            self._add_token(TokenType.INDENT, " " * indent)
        elif indent < current_indent:
            while self.indent_stack[-1] > indent:
                self.indent_stack.pop()
                self._add_token(TokenType.DEDENT, "")

    def _skip_comment(self):
        """Skip a comment until end of line."""
        while self._peek() not in "\n\0":
            self._advance()

    def _match_operator(self) -> bool:
        """Try to match a multi-char or single-char operator."""
        # Two-character operators
        two_char = self.source[self.pos:self.pos + 2]
        two_char_ops = {
            "<-": TokenType.ARROW_LEFT,
            "->": TokenType.ARROW_RIGHT,
            "<=": TokenType.LTE,
            ">=": TokenType.GTE,
            "==": TokenType.EQ,
            "!=": TokenType.NEQ,
            "..": TokenType.RANGE,
        }
        if two_char in two_char_ops:
            self._add_token(two_char_ops[two_char], two_char)
            self._advance()
            self._advance()
            return True

        # Single-character operators
        one_char_ops = {
            ":": TokenType.COLON,
            ",": TokenType.COMMA,
            ".": TokenType.DOT,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            "<": TokenType.LT,
            ">": TokenType.GT,
        }
        if self._peek() in one_char_ops:
            char = self._advance()
            self._add_token(one_char_ops[char], char)
            return True

        return False

    def _read_string(self):
        """Read a string literal."""
        self._advance()  # Skip opening quote
        start = self.pos
        while self._peek() != '"' and self._peek() != "\0":
            if self._peek() == "\n":
                raise LexerError("Unterminated string", self.line, self.column)
            self._advance()
        if self._peek() == "\0":
            raise LexerError("Unterminated string", self.line, self.column)
        value = self.source[start:self.pos]
        self._advance()  # Skip closing quote
        self._add_token(TokenType.STRING, value)

    def _read_number(self):
        """Read a number, possibly with sign and unit."""
        start = self.pos
        start_col = self.column

        # Handle sign
        if self._peek() in "+-":
            self._advance()

        # Read integer part
        while self._peek().isdigit():
            self._advance()

        # Read decimal part
        if self._peek() == "." and self._peek_ahead().isdigit():
            self._advance()  # Skip dot
            while self._peek().isdigit():
                self._advance()

        number_str = self.source[start:self.pos]
        self._add_token(TokenType.NUMBER, number_str)

        # Check for unit
        unit_start = self.pos
        # Handle degree symbol
        if self._peek() == "°":
            self._advance()
            if self._peek() in "CFK":
                self._advance()
                self._add_token(TokenType.UNIT, self.source[unit_start:self.pos])
                return

        # Handle % and other units
        if self._peek() == "%":
            self._advance()
            self._add_token(TokenType.UNIT, "%")
            return

        # Handle alphabetic units (ms, GB, etc.)
        if self._peek().isalpha():
            while self._peek().isalnum():
                self._advance()
            unit = self.source[unit_start:self.pos]
            if unit in self.UNITS or unit.lower() in ["ms", "s", "m", "h"]:
                self._add_token(TokenType.UNIT, unit)

    def _read_identifier(self):
        """Read an identifier or keyword."""
        start = self.pos
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        value = self.source[start:self.pos]
        lower_value = value.lower()

        # Check if it's a keyword
        if lower_value in self.KEYWORDS:
            self._add_token(self.KEYWORDS[lower_value], value)
        else:
            self._add_token(TokenType.IDENTIFIER, value)

    def _read_annotation(self):
        """Read an annotation like @version or @critical."""
        self._advance()  # Skip @
        start = self.pos
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        name = self.source[start:self.pos]
        name_lower = name.lower()

        annotation_types = {
            "version": TokenType.VERSION,
            "critical": TokenType.CRITICAL,
            "warning": TokenType.WARNING,
            "priority": TokenType.PRIORITY,
        }

        if name_lower in annotation_types:
            self._add_token(annotation_types[name_lower], name)
        else:
            raise LexerError(f"Unknown annotation: @{name}", self.line, self.column)
