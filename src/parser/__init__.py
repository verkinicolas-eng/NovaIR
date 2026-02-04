# NovaIR Parser
# A basic parser for the NovaIR declarative DSL

from .lexer import Lexer, Token, TokenType
from .parser import Parser
from .ast import (
    System, State, Constraint, Objective, Action, Tick,
    Effect, Parameter, SourcePath, ValueWithUnit
)

__version__ = "0.1.0"
__all__ = [
    "Lexer", "Token", "TokenType",
    "Parser",
    "System", "State", "Constraint", "Objective", "Action", "Tick",
    "Effect", "Parameter", "SourcePath", "ValueWithUnit",
    "parse_file", "parse_string"
]


def parse_file(filepath: str) -> "System":
    """Parse a .novair file and return the AST."""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    return parse_string(source)


def parse_string(source: str) -> "System":
    """Parse a NovaIR source string and return the AST."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()
