import re
from enum import IntEnum, auto
from typing import List, Tuple, Optional
from dataclasses import dataclass


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
    ANDALSO = auto()
    ORELSE = auto()
    NOPE = auto()
    
    # Boolean Constants
    TRUE = auto()
    FALSE = auto()
    NONE = auto()
    
    # Comparison Operators
    EQ = auto()        # ==
    NEQ = auto()       # !=
    LT = auto()        # <
    GT = auto()        # >
    LTE = auto()       # <=
    GTE = auto()       # >=
    
    # Arithmetic Operators
    PLUS = auto()      # +
    MINUS = auto()     # -
    MULTIPLY = auto()  # *
    DIVIDE = auto()    # /
    MODULO = auto()    # %
    
    # Assignment
    ASSIGN = auto()    # =
    
    # Delimiters and Separators
    SEMICOLON = auto()
    COLON = auto()
    COMMA = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    
    # Literals and Identifiers
    INTCON = auto()    # Integer constant
    FLOATCON = auto()  # Float constant
    STRCON = auto()    # String constant
    ID = auto()        # Identifier
    
    # Special
    EOF = auto()
    ERROR = auto()


@dataclass
class Token:
    """Represents a token with its type, lexeme, line, and column"""
    type: TokenType
    lexeme: str
    line: int
    column: int
    token_number: int
    literal_value: Optional[any] = None
    
    def to_parser_format(self) -> str:
        """Format for parser (token stream)"""
        # For literals, include the value/ID
        if self.type == TokenType.INTCON:
            return f"{self.line} {self.type.value} INTCON {self.literal_value}"
        elif self.type == TokenType.FLOATCON:
            return f"{self.line} {self.type.value} FLOATCON {self.literal_value}"
        elif self.type == TokenType.STRCON:
            return f"{self.line} {self.type.value} STRCON {self.literal_value}"
        elif self.type == TokenType.ID:
            return f"{self.line} {self.type.value} ID {self.lexeme}"
        else:
            return f"{self.line} {self.type.value} {self.type.name}"
    
    def to_debug_format(self) -> str:
        """Format for debugging display"""
        return f"Line {self.line} Token #{self.token_number}: {self.lexeme}"


class SymbolTable:
    """Manages symbols including reserved words and identifiers"""
    def __init__(self):
        self.symbols = {}
        self.next_id = 0
        self._initialize_reserved_words()
    
    def _initialize_reserved_words(self):
        """Initialize symbol table with all reserved words"""
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
            'andAlso': TokenType.ANDALSO,
            'orElse': TokenType.ORELSE,
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
        """Look up a symbol in the table"""
        return self.symbols.get(lexeme)
    
    def insert(self, lexeme: str, token_type: TokenType = TokenType.ID) -> dict:
        """Insert a new identifier into the symbol table"""
        if lexeme not in self.symbols:
            self.symbols[lexeme] = {
                'id': self.next_id,
                'token_type': token_type,
                'is_reserved': False
            }
            self.next_id += 1
        return self.symbols[lexeme]
    
    def print_table(self):
        """Print the symbol table in a readable format"""
        print("\n=== SYMBOL TABLE ===")
        print(f"{'ID':<5} {'Lexeme':<20} {'Token Type':<20} {'Reserved':<10}")
        print("-" * 60)
        for lexeme, info in sorted(self.symbols.items(), key=lambda x: x[1]['id']):
            print(f"{info['id']:<5} {lexeme:<20} {info['token_type'].name:<20} {info['is_reserved']}")


class LiteralTable:
    """Manages literal values (strings and numbers)"""
    def __init__(self):
        self.literals = {}
        self.next_id = 0
    
    def insert(self, value: any, literal_type: str) -> int:
        """Insert a literal and return its ID"""
        key = (literal_type, str(value))
        if key not in self.literals:
            self.literals[key] = {
                'id': self.next_id,
                'value': value,
                'type': literal_type
            }
            self.next_id += 1
        return self.literals[key]['id']
    
    def print_table(self):
        """Print the literal table in a readable format"""
        print("\n=== LITERAL TABLE ===")
        print(f"{'ID':<5} {'Type':<10} {'Value':<30}")
        print("-" * 50)
        for (lit_type, _), info in sorted(self.literals.items(), key=lambda x: x[1]['id']):
            value_str = repr(info['value'])[:27] + "..." if len(repr(info['value'])) > 30 else repr(info['value'])
            print(f"{info['id']:<5} {info['type']:<10} {value_str:<30}")


class Lexer:
    """Lexical analyzer for the cleaning agent language"""
    
    # Token patterns (order matters!)
    TOKEN_PATTERNS = [
        # Comments (must come before operators to catch //)
        (r'//[^\n]*', 'COMMENT'),
        
        # Multi-character operators (must come before single-character ones)
        (r'==', TokenType.EQ),
        (r'!=', TokenType.NEQ),
        (r'<=', TokenType.LTE),
        (r'>=', TokenType.GTE),
        
        # Keywords and identifiers (identifiers must come after keywords)
        (r'\b(?:andAlso|orElse|nope|True|False|None|task|define|do|until|check|otherwise|return|world|agent|move|turn|grab|drop|scan)\b', 'KEYWORD'),
        (r'[A-Za-z_][A-Za-z0-9_]*', TokenType.ID),
        
        # Numbers (integer or float)
        (r'\d+\.\d+', TokenType.FLOATCON),  # Float must come before int
        (r'\d+', TokenType.INTCON),
        
        # Strings (double or single quoted)
        (r'"(?:[^"\\]|\\.)*"', TokenType.STRCON),
        (r"'(?:[^'\\]|\\.)*'", TokenType.STRCON),
        
        # Single-character operators and delimiters
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
        
        # Whitespace (spaces, tabs, newlines)
        (r'[ \t\n\r]+', 'WHITESPACE'),
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
        self.token_counter = 0
    
    def error(self, message: str):
        """Record an error"""
        error_msg = f"Error at line {self.line}, column {self.column}: {message}"
        self.errors.append(error_msg)
        print(error_msg)
    
    def advance(self, count: int = 1):
        """Advance position and update line/column tracking"""
        for _ in range(count):
            if self.position < len(self.source):
                if self.source[self.position] == '\n':
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
                self.position += 1
    
    def match_keyword_or_identifier(self, lexeme: str, line: int, column: int, token_num: int) -> Token:
        """Determine if a lexeme is a keyword or identifier"""
        symbol_info = self.symbol_table.lookup(lexeme)
        
        if symbol_info and symbol_info['is_reserved']:
            return Token(symbol_info['token_type'], lexeme, line, column, token_num)
        else:
            self.symbol_table.insert(lexeme, TokenType.ID)
            return Token(TokenType.ID, lexeme, line, column, token_num)
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire source code"""
        while self.position < len(self.source):
            start_line = self.line
            start_column = self.column
            matched = False
            
            # Try to match each pattern
            for pattern, token_type in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(self.source, self.position)
                
                if match:
                    lexeme = match.group(0)
                    
                    # Skip whitespace and comments
                    if token_type == 'WHITESPACE' or token_type == 'COMMENT':
                        self.advance(len(lexeme))
                        matched = True
                        break
                    
                    self.token_counter += 1
                    
                    # Special handling for keywords/identifiers
                    if token_type == 'KEYWORD':
                        token = self.match_keyword_or_identifier(lexeme, start_line, start_column, self.token_counter)
                    elif token_type == TokenType.ID:
                        token = self.match_keyword_or_identifier(lexeme, start_line, start_column, self.token_counter)
                    elif token_type == TokenType.INTCON:
                        value = int(lexeme)
                        literal_id = self.literal_table.insert(value, 'int')
                        token = Token(token_type, lexeme, start_line, start_column, self.token_counter, value)
                    elif token_type == TokenType.FLOATCON:
                        value = float(lexeme)
                        literal_id = self.literal_table.insert(value, 'float')
                        token = Token(token_type, lexeme, start_line, start_column, self.token_counter, value)
                    elif token_type == TokenType.STRCON:
                        value = lexeme[1:-1]  # Remove quotes
                        literal_id = self.literal_table.insert(value, 'string')
                        token = Token(token_type, lexeme, start_line, start_column, self.token_counter, literal_id)
                    else:
                        token = Token(token_type, lexeme, start_line, start_column, self.token_counter)
                    
                    self.tokens.append(token)
                    self.advance(len(lexeme))
                    matched = True
                    break
            
            if not matched:
                char = self.source[self.position] if self.position < len(self.source) else ''
                self.error(f"Unexpected character: '{char}'")
                self.token_counter += 1
                self.tokens.append(Token(TokenType.ERROR, char, start_line, start_column, self.token_counter))
                self.advance()
        
        return self.tokens
    
    def print_output(self):
        """Print output in the format shown in the image"""
        print("\n" + "="*80)
        print("LEXICAL ANALYSIS OUTPUT")
        print("="*80)
        
        # Create two-column output
        print(f"\n{'To the Parser (token stream or file)':<45} | {'To the screen (for debugging purposes)'}")
        print("-"*45 + "+" + "-"*45)
        
        for token in self.tokens:
            parser_output = token.to_parser_format()
            debug_output = token.to_debug_format()
            print(f"{parser_output:<45} | {debug_output}")
    
    def write_token_file(self, filename: str = "tokens.txt"):
        """Write tokens to a file for parser input"""
        with open(filename, 'w') as f:
            for token in self.tokens:
                f.write(token.to_parser_format() + '\n')
        print(f"\n✓ Token stream written to '{filename}'")


# Example usage
if __name__ == "__main__":
    # Test with a simple example similar to the image
    test_code = """// Initialize Cleaning World Environment

WORLD_SIZE = 5;
DIRTY = True;
CLEAN = False;
STEPS = 0;

// Represent the grid as a simplified structure
define initializeWorld:
{
  i = 0;
  do
    row = i;
    // Normally would read from file, but here we simulate
    // Each cell starts as DIRTY
    markRowAsDirty(row);
    i = i + 1;
  until i >= WORLD_SIZE;
  return;
}

// Function to clean a specific cell
define cleanCell:
{
  check currentCell == DIRTY:
  {
    currentCell = CLEAN;
    cleanedCount = cleanedCount + 1;
    log("Cell cleaned!");
  }
  otherwise:
  {
    log("Cell already clean.");
  }
  return;
}

// Function to move the agent to the next cell
define moveNext:
{
  STEPS = STEPS + 1;
  currentColumn = currentColumn + 1;
  check currentColumn >= WORLD_SIZE:
  {
    currentColumn = 0;
    currentRow = currentRow + 1;
  }
  return;
}

// Task to clean the entire world
task cleanWorld:
{
  cleanedCount = 0;
  currentRow = 0;
  currentColumn = 0;

  do
    currentCell = DIRTY;  // simulate reading the cell
    cleanCell();
    moveNext();
  until currentRow >= WORLD_SIZE;

  check cleanedCount > 0:
  {
    log("World successfully cleaned!");
  }
  otherwise:
  {
    log("Nothing to clean.");
  }
}

// Function for simple logging (print simulation)
define log:
{
  // In a real system, this might write to file or console
  return;
}

// Main entry point
define main:
{
  initializeWorld();
  cleanWorld();
  log("Cleaning complete after " + STEPS + " steps.");
  return;
}

// Program execution starts here
main();
"""
    
    print("SOURCE CODE:")
    print("-" * 40)
    print(test_code)
    print("-" * 40)
    
    lexer = Lexer(test_code)
    tokens = lexer.tokenize()
    
    # Print output in the required format
    lexer.print_output()
    
    # Optionally write to file
    lexer.write_token_file()
    
    # Print tables
    lexer.symbol_table.print_table()
    lexer.literal_table.print_table()
    
    if lexer.errors:
        print("\n=== ERRORS ===")
        for error in lexer.errors:
            print(error)
    else:
        print("\n✓ Lexical analysis completed successfully!")
    
    print(f"\nTotal tokens: {len(tokens)}")