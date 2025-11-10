import re
import argparse
from enum import IntEnum, auto
from typing import List, Optional
from dataclasses import dataclass
import sys


class TokenType(IntEnum):
    """Token type constants for the lexer"""
    # Keywords
    TASK = auto()
    DEFINE = auto()
    DO = auto()
    UNTIL = auto()
    CHECK = auto()
    OTHERWISE = auto()
    RETURN = auto()
    WORLD = auto()
    AGENT = auto()
    
    # Built-in Functions
    MOVE = auto()
    TURN = auto()
    GRAB = auto()
    DROP = auto()
    SCAN = auto()
    
    # Logical Operators
    AND_ALSO = auto()
    OR_ELSE = auto()
    NOPE = auto()
    
    # Boolean Constants
    TRUE = auto()
    FALSE = auto()
    NONE = auto()
    
    # Comparison Operators
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    
    # Arithmetic Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    
    # Assignment
    ASSIGN = auto()
    
    # Delimiters and Separators
    SEMICOLON = auto()
    COLON = auto()
    COMMA = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    
    # Literals and Identifiers
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    
    # Special
    COMMENT = auto()
    WHITESPACE = auto()
    EOF = auto()
    ERROR = auto()


@dataclass
class Token:
    """Represents a token with its type, lexeme, line, and column"""
    type: TokenType
    lexeme: str
    line: int
    column: int
    literal_value: Optional[any] = None
    
    def __repr__(self):
        if self.literal_value is not None:
            return f"Token({self.type.name}, '{self.lexeme}', {self.line}:{self.column}, value={self.literal_value})"
        return f"Token({self.type.name}, '{self.lexeme}', {self.line}:{self.column})"


class SymbolTable:
    """Manages symbols including reserved words and identifiers"""
    def __init__(self):
        self.symbols = {}
        self.next_id = 0
        self._initialize_reserved_words()
    
    def _initialize_reserved_words(self):
        reserved = {
            'task': TokenType.TASK,
            'define': TokenType.DEFINE,
            'do': TokenType.DO,
            'until': TokenType.UNTIL,
            'check': TokenType.CHECK,
            'otherwise': TokenType.OTHERWISE,
            'return': TokenType.RETURN,
            'world': TokenType.WORLD,
            'agent': TokenType.AGENT,
            'move': TokenType.MOVE,
            'turn': TokenType.TURN,
            'grab': TokenType.GRAB,
            'drop': TokenType.DROP,
            'scan': TokenType.SCAN,
            'andAlso': TokenType.AND_ALSO,
            'orElse': TokenType.OR_ELSE,
            'nope': TokenType.NOPE,
            'True': TokenType.TRUE,
            'False': TokenType.FALSE,
            'None': TokenType.NONE,
        }
        
        for lexeme, token_type in reserved.items():
            self.symbols[lexeme] = {
                'id': self.next_id,
                'token_type': token_type,
                'is_reserved': True
            }
            self.next_id += 1
    
    def lookup(self, lexeme: str) -> Optional[dict]:
        return self.symbols.get(lexeme)
    
    def insert(self, lexeme: str, token_type: TokenType = TokenType.IDENTIFIER) -> dict:
        if lexeme not in self.symbols:
            self.symbols[lexeme] = {
                'id': self.next_id,
                'token_type': token_type,
                'is_reserved': False
            }
            self.next_id += 1
        return self.symbols[lexeme]
    
    def print_table(self, output_stream=sys.stdout):
        print("\n=== SYMBOL TABLE ===", file=output_stream)
        print(f"{'ID':<5} {'Lexeme':<20} {'Token Type':<20} {'Reserved':<10}", file=output_stream)
        print("-" * 60, file=output_stream)
        for lexeme, info in sorted(self.symbols.items(), key=lambda x: x[1]['id']):
            print(f"{info['id']:<5} {lexeme:<20} {info['token_type'].name:<20} {info['is_reserved']}", file=output_stream)


class LiteralTable:
    """Manages literal values (strings and numbers)"""
    def __init__(self):
        self.literals = {}
        self.next_id = 0
    
    def insert(self, value: any, literal_type: str) -> int:
        key = (literal_type, str(value))
        if key not in self.literals:
            self.literals[key] = {
                'id': self.next_id,
                'value': value,
                'type': literal_type
            }
            self.next_id += 1
        return self.literals[key]['id']
    
    def print_table(self, output_stream=sys.stdout):
        print("\n=== LITERAL TABLE ===", file=output_stream)
        print(f"{'ID':<5} {'Type':<10} {'Value':<30}", file=output_stream)
        print("-" * 50, file=output_stream)
        for (lit_type, _), info in sorted(self.literals.items(), key=lambda x: x[1]['id']):
            value_str = repr(info['value'])[:27] + "..." if len(repr(info['value'])) > 30 else repr(info['value'])
            print(f"{info['id']:<5} {info['type']:<10} {value_str:<30}", file=output_stream)


class Lexer:
    """Lexical analyzer for the cleaning agent language"""
    TOKEN_PATTERNS = [
        (r'//[^\n]*', TokenType.COMMENT),
        (r'==', TokenType.EQ),
        (r'!=', TokenType.NEQ),
        (r'<=', TokenType.LTE),
        (r'>=', TokenType.GTE),
        (r'\b(?:andAlso|orElse|nope|True|False|None|task|define|do|until|check|otherwise|return|world|agent|move|turn|grab|drop|scan)\b', None),
        (r'[A-Za-z_][A-Za-z0-9_]*', TokenType.IDENTIFIER),
        (r'\d+\.?\d*', TokenType.NUMBER),
        (r'"(?:[^"\\]|\\.)*"', TokenType.STRING),
        (r"'(?:[^'\\]|\\.)*'", TokenType.STRING),
        (r'<', TokenType.LT),
        (r'>', TokenType.GT),
        (r'\+', TokenType.PLUS),
        (r'-', TokenType.MINUS),
        (r'\*', TokenType.MULTIPLY),
        (r'/', TokenType.DIVIDE),
        (r'%', TokenType.MODULO),
        (r'=', TokenType.ASSIGN),
        (r';', TokenType.SEMICOLON),
        (r':', TokenType.COLON),
        (r',', TokenType.COMMA),
        (r'\(', TokenType.LPAREN),
        (r'\)', TokenType.RPAREN),
        (r'\{', TokenType.LBRACE),
        (r'\}', TokenType.RBRACE),
        (r'[ \t\n\r]+', TokenType.WHITESPACE),
    ]
    
    def __init__(self, source_code: str):
        self.source = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.symbol_table = SymbolTable()
        self.literal_table = LiteralTable()
        self.errors: List[str] = []
    
    def error(self, message: str):
        error_msg = f"Error at line {self.line}, column {self.column}: {message}"
        self.errors.append(error_msg)
        print(error_msg)
    
    def peek(self, offset: int = 0) -> Optional[str]:
        pos = self.position + offset
        return self.source[pos] if pos < len(self.source) else None
    
    def advance(self, count: int = 1):
        for _ in range(count):
            if self.position < len(self.source):
                if self.source[self.position] == '\n':
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
                self.position += 1
    
    def match_keyword_or_identifier(self, lexeme: str, line: int, column: int) -> Token:
        symbol_info = self.symbol_table.lookup(lexeme)
        if symbol_info and symbol_info['is_reserved']:
            return Token(symbol_info['token_type'], lexeme, line, column)
        else:
            self.symbol_table.insert(lexeme, TokenType.IDENTIFIER)
            return Token(TokenType.IDENTIFIER, lexeme, line, column)
    
    def tokenize(self) -> List[Token]:
        while self.position < len(self.source):
            start_line = self.line
            start_column = self.column
            matched = False
            
            for pattern, token_type in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(self.source, self.position)
                if match:
                    lexeme = match.group(0)
                    if token_type in [TokenType.WHITESPACE, TokenType.COMMENT]:
                        self.advance(len(lexeme))
                        matched = True
                        break
                    
                    if token_type is None:
                        token = self.match_keyword_or_identifier(lexeme, start_line, start_column)
                    elif token_type == TokenType.IDENTIFIER:
                        token = self.match_keyword_or_identifier(lexeme, start_line, start_column)
                    elif token_type == TokenType.NUMBER:
                        value = float(lexeme) if '.' in lexeme else int(lexeme)
                        self.literal_table.insert(value, 'number')
                        token = Token(token_type, lexeme, start_line, start_column, value)
                    elif token_type == TokenType.STRING:
                        value = lexeme[1:-1]
                        self.literal_table.insert(value, 'string')
                        token = Token(token_type, lexeme, start_line, start_column, value)
                    else:
                        token = Token(token_type, lexeme, start_line, start_column)
                    
                    self.tokens.append(token)
                    self.advance(len(lexeme))
                    matched = True
                    break
            
            if not matched:
                char = self.peek()
                self.error(f"Unexpected character: '{char}'")
                self.tokens.append(Token(TokenType.ERROR, char, start_line, start_column))
                self.advance()
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens
    
    def print_tokens(self, output_stream=sys.stdout):
        print("\n=== TOKENS ===", file=output_stream)
        print(f"{'#':<5} {'Type':<20} {'Lexeme':<25} {'Position':<15} {'Value':<20}", file=output_stream)
        print("-" * 90, file=output_stream)
        for i, token in enumerate(self.tokens):
            lexeme_display = token.lexeme[:22] + "..." if len(token.lexeme) > 25 else token.lexeme
            position = f"{token.line}:{token.column}"
            value_str = str(token.literal_value) if token.literal_value is not None else ""
            print(f"{i:<5} {token.type.name:<20} {lexeme_display:<25} {position:<15} {value_str:<20}", file=output_stream)


def main():
    parser = argparse.ArgumentParser(description="Lexical Analyzer CLI")
    parser.add_argument("--input", help="Path to input source file", required=False)
    parser.add_argument("--output", help="Path to output tokens file", required=False)
    args = parser.parse_args()

    if not args.input or not args.output:
        print("Usage: python LexicalAnalysis.py --input file.txt --output tokens.txt")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        source_code = f.read()

    lexer = Lexer(source_code)
    tokens = lexer.tokenize()

    print("=" * 80)
    print("LEXICAL ANALYSIS")
    print("=" * 80)

    # Print everything to terminal
    lexer.print_tokens()
    lexer.symbol_table.print_table()
    lexer.literal_table.print_table()

    if lexer.errors:
        print("\n=== ERRORS ===")
        for error in lexer.errors:
            print(error)
    else:
        print("\n✓ Lexical analysis completed successfully with no errors!")

    print(f"\nTotal tokens: {len(tokens)}")
    print(f"Total symbols: {len(lexer.symbol_table.symbols)}")
    print(f"Total literals: {len(lexer.literal_table.literals)}")

    # Now export ONLY tokens section to output file
    from io import StringIO
    token_buffer = StringIO()
    lexer.print_tokens(token_buffer)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(token_buffer.getvalue())


if __name__ == "__main__":
    main()
