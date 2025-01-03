import pytest
from scim_filter_parser.lexer import (
    Lexer, Token, 
    NumericLiteralToken, StringLiteralToken, TrueLiteralToken, FalseLiteralToken, NullLiteralToken,
    PresenceOperatorToken, ComparisonOperatorToken,
    ComplexFilterGroupStartToken, ComplexFilterGroupEndToken,
    LogicOperatorToken, PrecedenceGroupEndToken, PrecedenceGroupStartToken
)
from scim_filter_parser.err_strings import (
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
    _unexpected_space,
)

# The following are taken from the RFC
valid_examples_from_rfc = {
    'filter=userName eq "bjensen"': [
        Token(value='userName', position=7),
        ComparisonOperatorToken(value='eq', position=16),
        StringLiteralToken(value='"bjensen"', position=19)
    ],
    'filter=name.familyName co "O\'Malley"' : [
        Token(value='name.familyName', position=7),
        ComparisonOperatorToken(value='co', position=23),
        StringLiteralToken(value='"O\'Malley"', position=26)
    ],
    'filter=userName sw "J"' : [
        Token(value='userName', position=7),
        ComparisonOperatorToken(value='sw', position=16),
        StringLiteralToken(value='"J"', position=19)
    ],
    'filter=urn:ietf:params:scim:schemas:core:2.0:User:userName sw "J"' : [
        Token(value='urn:ietf:params:scim:schemas:core:2.0:User:userName', position=7),
        ComparisonOperatorToken(value='sw', position=59),
        StringLiteralToken(value='"J"', position=62)
    ],
    'filter=title pr' : [
        Token(value='title', position=7),
        PresenceOperatorToken(value='pr', position=13)
    ],
    'filter=meta.lastModified gt "2011-05-13T04:42:34Z"' : [
        Token(value='meta.lastModified', position=7),
        ComparisonOperatorToken(value='gt', position=25),
        StringLiteralToken(value='"2011-05-13T04:42:34Z"', position=28)
    ],
    'filter=meta.lastModified ge "2011-05-13T04:42:34Z"' : [
        Token(value='meta.lastModified', position=7),
        ComparisonOperatorToken(value='ge', position=25),
        StringLiteralToken(value='"2011-05-13T04:42:34Z"', position=28)
    ],
    'filter=meta.lastModified lt "2011-05-13T04:42:34Z"' : [
        Token(value='meta.lastModified', position=7),
        ComparisonOperatorToken(value='lt', position=25),
        StringLiteralToken(value='"2011-05-13T04:42:34Z"', position=28)
    ],
    'filter=meta.lastModified le "2011-05-13T04:42:34Z"' : [
        Token(value='meta.lastModified', position=7),
        ComparisonOperatorToken(value='le', position=25),
        StringLiteralToken(value='"2011-05-13T04:42:34Z"', position=28)
    ],
    'filter=title pr and userType eq "Employee"' : [
        Token(value='title', position=7),
        PresenceOperatorToken(value='pr', position=13),
        LogicOperatorToken(value='and', position=16),
        Token(value='userType', position=20),
        ComparisonOperatorToken(value='eq', position=29),
        StringLiteralToken(value='"Employee"', position=32),
    ],
    'filter=title pr or userType eq "Intern"' : [
        Token(value='title', position=7),
        PresenceOperatorToken(value='pr', position=13),
        LogicOperatorToken(value='or', position=16),
        Token(value='userType', position=19),
        ComparisonOperatorToken(value='eq', position=28),
        StringLiteralToken(value='"Intern"', position=31)
    ],
    'filter=schemas eq "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"' : [
        Token(value='schemas', position=7),
        ComparisonOperatorToken(value='eq', position=15),
        StringLiteralToken(value='"urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"', position=18)
    ],
    'filter=userType eq "Employee" and (emails co "example.com" or emails.value co "example.org")' : [
        Token(value='userType', position=7),
        ComparisonOperatorToken(value='eq', position=16),
        StringLiteralToken(value='"Employee"', position=19),
        LogicOperatorToken(value='and', position=30),
        PrecedenceGroupStartToken(value='(', position=34),
        Token(value='emails', position=35),
        ComparisonOperatorToken(value='co', position=42),
        StringLiteralToken(value='"example.com"', position=45),
        LogicOperatorToken(value='or', position=59),
        Token(value='emails.value', position=62),
        ComparisonOperatorToken(value='co', position=75),
        StringLiteralToken(value='"example.org"', position=78),
        PrecedenceGroupEndToken(value=')', position=91)
    ],
    'filter=userType ne "Employee" and not (emails co "example.com" or emails.value co "example.org")' : [
        Token(value='userType', position=7),
        ComparisonOperatorToken(value='ne', position=16),
        StringLiteralToken(value='"Employee"', position=19),
        LogicOperatorToken(value='and', position=30),
        LogicOperatorToken(value='not', position=34),
        PrecedenceGroupStartToken(value='(', position=38),
        Token(value='emails', position=39),
        ComparisonOperatorToken(value='co', position=46),
        StringLiteralToken(value='"example.com"', position=49),
        LogicOperatorToken(value='or', position=63),
        Token(value='emails.value', position=66),
        ComparisonOperatorToken(value='co', position=79),
        StringLiteralToken(value='"example.org"', position=82),
        PrecedenceGroupEndToken(value=')', position=95)
    ],
    'filter=userType eq "Employee" and (emails.type eq "work")' : [
        Token(value='userType', position=7),
        ComparisonOperatorToken(value='eq', position=16),
        StringLiteralToken(value='"Employee"', position=19),
        LogicOperatorToken(value='and', position=30),
        PrecedenceGroupStartToken(value='(', position=34),
        Token(value='emails.type', position=35),
        ComparisonOperatorToken(value='eq', position=47),
        StringLiteralToken(value='"work"', position=50),
        PrecedenceGroupEndToken(value=')', position=56)
    ],
    'filter=userType eq "Employee" and emails[type eq "work" and value co "@example.com"]' : [
        Token(value='userType', position=7),
        ComparisonOperatorToken(value='eq', position=16),
        StringLiteralToken(value='"Employee"', position=19),
        LogicOperatorToken(value='and', position=30),
        Token(value='emails', position=34),
        ComplexFilterGroupStartToken(value='[', position=40),
        Token(value='type', position=41),
        ComparisonOperatorToken(value='eq', position=46),
        StringLiteralToken(value='"work"', position=49),
        LogicOperatorToken(value='and', position=56),
        Token(value='value', position=60),
        ComparisonOperatorToken(value='co', position=66),
        StringLiteralToken(value='"@example.com"', position=69),
        ComplexFilterGroupEndToken(value=']', position=83)],
    'filter=emails[type eq "work" and value co "@example.com"] or ims[type eq "xmpp" and value co "@foo.com"]' : [
        Token(value='emails', position=7),
        ComplexFilterGroupStartToken(value='[', position=13),
        Token(value='type', position=14),
        ComparisonOperatorToken(value='eq', position=19),
        StringLiteralToken(value='"work"', position=22),
        LogicOperatorToken(value='and', position=29),
        Token(value='value', position=33),
        ComparisonOperatorToken(value='co', position=39),
        StringLiteralToken(value='"@example.com"', position=42),
        ComplexFilterGroupEndToken(value=']', position=56),
        LogicOperatorToken(value='or', position=58),
        Token(value='ims', position=61),
        ComplexFilterGroupStartToken(value='[', position=64),
        Token(value='type', position=65),
        ComparisonOperatorToken(value='eq', position=70),
        StringLiteralToken(value='"xmpp"', position=73),
        LogicOperatorToken(value='and', position=80),
        Token(value='value', position=84),
        ComparisonOperatorToken(value='co', position=90),
        StringLiteralToken(value='"@foo.com"', position=93),
        ComplexFilterGroupEndToken(value=']', position=103)
    ],
}

def test_valid_example_filters_from_rfc():
    for k, v in valid_examples_from_rfc.items():
        print(f"Testing example filter: {k}")
        lexer = Lexer(k)
        tokens = [x for x in lexer]
        # print(tokens)
        # print(v)
        assert tokens == v
        break

def test_space_before_attribute_group_open():
    f = 'filter=emails [type eq "work" and value co "@example.com"]'
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == f"{_no_spaces_before_complex_group_open} 14"
        
def test_space_after_attribute_group_open():
    f = 'filter=emails[ type eq "work" and value co "@example.com"]'
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == f"{_no_spaces_after_complex_group_open} 14"

def test_space_before_attribute_group_close():
    f = 'filter=emails[type eq "work" and value co "@example.com" ]'
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == f"{_no_spaces_before_complex_group_close} 57"

def test_missing_space_after_attribute_group_close():
    f = 'filter=emails[type eq "work"]and value co "@example.com"'
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == f"{_missing_space_after_complex_group_close} 28"

def test_missing_space_before_logic_group_open():
    f = 'filter=userType eq "Employee" and(emails.type eq "work")' 
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == f"{_missing_space_before_precedence_group_open} 33"
        
def test_space_after_logic_group_open():
    f = 'filter=userType eq "Employee" and ( emails.type eq "work")' 
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == f"{_no_spaces_after_precedence_group_open} 34"

def test_valid_numeric_literal():
    f = 'filter=userType eq 7657' 
    lexer = Lexer(f)
    tokens = [x for x in lexer]
    print(tokens)
    assert tokens == [
        Token("userType", 7),
        ComparisonOperatorToken("eq", 16),
        NumericLiteralToken("7657", 19),
    ]

def test_invalid_numeric_literal():
    f = 'filter=userType eq 7657sa387090' 
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == f"{_invalid_numeric_literal} 19"
        
def test_valid_true_literal():
    f = 'filter=userType eq true' 
    lexer = Lexer(f)
    tokens = [x for x in lexer]
    print(tokens)
    assert tokens == [
        Token("userType", 7),
        ComparisonOperatorToken("eq", 16),
        TrueLiteralToken("true", 19),
    ]
    
def test_truncated_true_literal():
    f = 'filter=userType eq tr ' 
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == _unexpected_end_of_input
        
def test_wrong_true_literal():
    f = 'filter=userType eq trello' 
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == f"{_unexpected_character} {21}"
        
def test_valid_false_literal():
    f = 'filter=userType eq false' 
    lexer = Lexer(f)
    tokens = [x for x in lexer]
    print(tokens)
    assert tokens == [
        Token("userType", 7),
        ComparisonOperatorToken("eq", 16),
        FalseLiteralToken("false", 19),
    ]
    
def test_truncated_false_literal():
    f = 'filter=userType eq fa ' 
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == _unexpected_end_of_input
        
def test_wrong_false_literal():
    f = 'filter=userType eq flase' 
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == f"{_unexpected_character} {20}"

def test_valid_null_literal():
    f = 'filter=userType eq null' 
    lexer = Lexer(f)
    tokens = [x for x in lexer]
    print(tokens)
    assert tokens == [
        Token("userType", 7),
        ComparisonOperatorToken("eq", 16),
        NullLiteralToken("null", 19),
    ]
    
def test_truncated_null_literal():
    f = 'filter=userType eq nu ' 
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == _unexpected_end_of_input
        
def test_wrong_null_literal():
    f = 'filter=userType eq nu   ' 
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == f"{_unexpected_character} {20}"
        
        
def test_valid_string_literal():
    f = 'filter=userType eq "Hello there!"' 
    lexer = Lexer(f)
    tokens = [x for x in lexer]
    print(tokens)
    assert tokens == [
        Token("userType", 7),
        ComparisonOperatorToken("eq", 16),
        StringLiteralToken('"Hello there!"', 19),
    ]
    
def test_truncated_string_literal():
    f = 'filter=userType eq "Hello the' 
    lexer = Lexer(f)
    with pytest.raises(ValueError) as e:
        _ = [x for x in lexer]
        assert str(e) == _unterminated_string