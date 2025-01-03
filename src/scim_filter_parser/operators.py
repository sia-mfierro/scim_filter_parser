
_precedence_open_lit = "("
_precedence_close_lit = ")"
_attribute_filter_open_lit = "["
_attribute_filter_close_lit = "]"
# Present operator (simplest attrExpr)
_present_op = "pr"
# Comparison operators
_equal_op = "eq"
_not_equal_op = "ne"
_contains_op = "co"
_starts_with_op = "sw"
_ends_with_op = "ew"
_greater_than_op = "gt"
_less_than_op = "lt"
_greater_than_or_equal_op = "ge"
_less_than_or_equal_op = "le"
_comparison_ops = [
    _equal_op, _not_equal_op, _contains_op, 
    _starts_with_op, _ends_with_op,
    _greater_than_op, _greater_than_or_equal_op,
    _less_than_op, _less_than_or_equal_op
]
# Logical operators
_and_op = "and"
_or_op = "or"
_logic_ops = [_and_op, _or_op]
# Not operator
_not_op = "not"