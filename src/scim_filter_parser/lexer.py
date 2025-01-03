import re
from enum import Enum
from dataclasses import dataclass
from .operators import (
    _present_op, _logic_ops, _comparison_ops, 
    _precedence_open_lit, _precedence_close_lit, 
    _attribute_filter_open_lit, _attribute_filter_close_lit
)
from .err_strings import (
    _no_spaces_before_complex_group_open,
    _no_spaces_after_complex_group_open,
    _no_spaces_before_complex_group_close,
    _missing_space_after_complex_group_close,
    _missing_space_before_precedence_group_open,
    _no_spaces_after_precedence_group_open,
    _invalid_numeric_literal,
    _unexpected_character,
    _unexpected_end_of_input,
    _unterminated_string,
)

digit_program = re.compile(r"\d")
alpha_program = re.compile(r"[a-zA-Z]")
namechar_program = re.compile(r"[a-zA-Z0-9_\-]")

def isspace(string):
    # In https://datatracker.ietf.org/doc/html/rfc5234
    # SP = %x20
    # So we really shouldn't be using str.isspace()
    if len(string) > 1:
        return ValueError("Expecting single character")
    return string == " "

@dataclass
class Token():
    value :str
    position: int

class Token(Token):
    pass

class ComparisonValueToken(Token):
    pass

class FalseLiteralToken(ComparisonValueToken):
    pass

class TrueLiteralToken(ComparisonValueToken):
    pass

class NullLiteralToken(ComparisonValueToken):
    pass

class NumericLiteralToken(ComparisonValueToken):
    pass

class StringLiteralToken(ComparisonValueToken):
    pass

class PrecedenceGroupStartToken(Token):
    pass

class PrecedenceGroupEndToken(Token):
    pass

class ComplexFilterGroupStartToken(Token):
    pass

class ComplexFilterGroupEndToken(Token):
    pass

class LogicOperatorToken(Token):
    pass

class ComparisonOperatorToken(Token):
    pass

class PresenceOperatorToken(Token):
    pass

class Lexer():
    leading_str = "filter="
    
    class State(Enum):
        Filter = 0
        ComparisonValue = 1
        StringLiteral = 2
        NumericLiteral = 3
        TrueLiteral = 4
        FalseLiteral = 5
        NullLiteral = 6
        
    
    def __init__(self, filter_str :str):
        self._position = -1
        if not filter_str:
            raise ValueError("Filter string cannot be emtpy")
        if not filter_str.startswith(Lexer.leading_str):
            raise ValueError(f"Invalid SCIM filter string. Expecting 'filter=' at position {self._position}")
        else:
            self._filter_str :str = filter_str
            self._position :int = len(Lexer.leading_str)-1
            self._state :Lexer.State = Lexer.State.Filter
    
    def __iter__(self):
        return self

    def __next__(self):
        return self.next_token()

    def emit_token(self, cls :type, start_pos :int, end_pos :int):
        return cls(self._filter_str[start_pos:end_pos+1], start_pos)

    def match_literal_op(self, op :str):
        filter_len = len(self._filter_str)
        op_len = len(op)
        if self._position + op_len <= filter_len:
            return self._filter_str[self._position:self._position + op_len] == op
        return False

    def next_token(self):
        token_start_position = None
        filter_len = len(self._filter_str)
        token = None
        
        while (
            self._position < filter_len-1
        ):
            self._position += 1
            current_character = self._filter_str[self._position]
            previous_character = self._filter_str[self._position-1] if self._position > 0 else None
            next_character = self._filter_str[self._position+1] if self._position < filter_len-1 else None
            
            eof = self._position == filter_len-1
            
            if self._state == Lexer.State.Filter:
                if current_character.isspace():
                    continue
                
                if token_start_position is None:
                    token_start_position = self._position
                    
                if current_character == _attribute_filter_open_lit:
                    if next_character and next_character.isspace():
                        raise ValueError(f"{_no_spaces_after_complex_group_open} {self._position}")
                    if previous_character and previous_character.isspace():
                        raise ValueError(f"{_no_spaces_before_complex_group_open} {self._position}")
                    if (previous_character and not previous_character.isspace()) or eof:
                        token = self.emit_token(ComplexFilterGroupStartToken, token_start_position, self._position)
                        break
                    ValueError(f"Unexpected attribute group open at positon: {self._position}")
                elif current_character == _attribute_filter_close_lit:
                    if next_character and not next_character.isspace():
                        raise ValueError(f"{_missing_space_after_complex_group_close} {self._position}")
                    if previous_character and previous_character.isspace():
                        raise ValueError(f"{_no_spaces_before_complex_group_close} {self._position}")
                    if (previous_character and not previous_character.isspace()) or eof:
                        token = self.emit_token(ComplexFilterGroupEndToken, token_start_position, self._position)
                        break
                    ValueError(f"Unexpected attribute group close at positon: {self._position}")
                elif current_character == _precedence_open_lit:
                    if next_character and next_character.isspace():
                        raise ValueError(f"{_no_spaces_after_precedence_group_open} {self._position}")
                    if previous_character and not previous_character.isspace():
                        raise ValueError(f"{_missing_space_before_precedence_group_open} {self._position}")
                    if token_start_position == self._position and (previous_character.isspace() or eof):
                        token = self.emit_token(PrecedenceGroupStartToken, token_start_position, self._position)
                        break
                    ValueError(f"Unexpected logic group open at positon: {self._position}")
                elif current_character == _precedence_close_lit:
                    if token_start_position == self._position and previous_character and previous_character.isspace():
                        raise ValueError(f"No spaces allowed before logic group closing at position: {self._position}")
                    if token_start_position == self._position and next_character and not next_character.isspace():
                        raise ValueError(f"Missing space after logic group closing at position: {self._position}")
                    if token_start_position == self._position and (previous_character.isspace() or eof):
                        token = self.emit_token(PrecedenceGroupEndToken, token_start_position, self._position)
                        break
                    raise ValueError(f"Unexpected logic group open at positon: {self._position}")
                elif (next_character and (next_character.isspace() or next_character == _attribute_filter_open_lit)) or eof:
                    token :Token = self.emit_token(Token, token_start_position, self._position)
                    if token.value in _comparison_ops:
                        token = ComparisonOperatorToken(value=token.value, position=token.position)
                        self._state = Lexer.State.ComparisonValue
                    elif token.value in _logic_ops:
                        token = LogicOperatorToken(value=token.value, position=token.position)
                    elif token.value == _present_op:
                        token = PresenceOperatorToken(value=token.value, position=token.position)
                    break                        
            elif self._state == Lexer.State.ComparisonValue:
                if current_character.isspace():
                    continue
            
                if token_start_position is None:
                    token_start_position = self._position
                
                if digit_program.fullmatch(current_character) and token_start_position == self._position:
                    self._state = Lexer.State.NumericLiteral
                elif current_character == "t" and token_start_position == self._position: 
                    self._state = Lexer.State.TrueLiteral
                elif current_character == "f" and token_start_position == self._position:
                    self._state = Lexer.State.FalseLiteral
                elif current_character == "n" and token_start_position == self._position:
                    self._state = Lexer.State.NullLiteral
                elif current_character == "\"" and token_start_position == self._position:
                    self._state = Lexer.State.StringLiteral
                else:
                    raise ValueError(f"{_unexpected_character} {self._position}")
            elif self._state == Lexer.State.NumericLiteral:
                if eof or (next_character and next_character.isspace()):
                    self._state = Lexer.State.Filter
                    token = self.emit_token(NumericLiteralToken, token_start_position, self._position)
                    break
                if not digit_program.fullmatch(current_character):
                    raise ValueError(f"{_invalid_numeric_literal} {self._position}")
            elif self._state == Lexer.State.TrueLiteral:
                # We already have a "t"
                if filter_len-token_start_position < 4:
                    raise ValueError(_unexpected_end_of_input)
                s = "rue"
                for i, c in enumerate(s):
                    if self._filter_str[self._position+i] != c:
                        raise ValueError(f"{_unexpected_character} {self._position+1}")
                if self._position+len(s) < filter_len and not self._filter_str[self._position+len(s)].isspace():
                    raise ValueError(f"{_unexpected_character} {self._position+len(s)}")
                self._state = Lexer.State.Filter
                self._position = self._position+len(s)-1
                token = self.emit_token(TrueLiteralToken, token_start_position, self._position)
                break
            elif self._state == Lexer.State.FalseLiteral:
                # We already have a "f"
                if filter_len-token_start_position < 5:
                    raise ValueError()
                s = "alse"
                for i, c in enumerate(s):
                    if self._filter_str[self._position+i] != c:
                        raise ValueError(f"{_unexpected_character} {self._position+1}")
                if self._position+len(s) < filter_len and not self._filter_str[self._position+len(s)].isspace():
                    raise ValueError(f"{_unexpected_character} {self._position+len(s)}")
                self._state = Lexer.State.Filter
                self._position = self._position+len(s)-1
                token = self.emit_token(FalseLiteralToken, token_start_position, self._position)
                break
            elif self._state == Lexer.State.NullLiteral:
                # We already have a "n"
                if filter_len-token_start_position < 4:
                    raise ValueError(_unexpected_end_of_input)
                s = "ull"
                for i, c in enumerate(s):
                    if self._filter_str[self._position+i] != c:
                        raise ValueError(f"{_unexpected_character} {self._position+1}")
                if self._position+len(s) < filter_len and not self._filter_str[self._position+len(s)].isspace():
                    raise ValueError(f"{_unexpected_character} {self._position+len(s)}")
                self._state = Lexer.State.Filter
                self._position = self._position+len(s)-1
                token = self.emit_token(NullLiteralToken, token_start_position, self._position)
                break
            elif self._state == Lexer.State.StringLiteral:
                # We will not test the validity of the string itself, e.g. escape characters
                # beyond the double quote escape
                if (current_character == '"' and previous_character != "\\"):
                    self._state = Lexer.State.Filter
                    token = self.emit_token(StringLiteralToken, token_start_position, self._position)
                    break
                elif eof:
                    raise ValueError(_unterminated_string)
        # print(token, self._state, flush=True)
        if token is None:
            raise StopIteration
        return token