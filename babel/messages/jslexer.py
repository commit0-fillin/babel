"""
    babel.messages.jslexer
    ~~~~~~~~~~~~~~~~~~~~~~

    A simple JavaScript 1.5 lexer which is used for the JavaScript
    extractor.

    :copyright: (c) 2013-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import annotations
import re
from collections.abc import Generator
from typing import NamedTuple
operators: list[str] = sorted(['+', '-', '*', '%', '!=', '==', '<', '>', '<=', '>=', '=', '+=', '-=', '*=', '%=', '<<', '>>', '>>>', '<<=', '>>=', '>>>=', '&', '&=', '|', '|=', '&&', '||', '^', '^=', '(', ')', '[', ']', '{', '}', '!', '--', '++', '~', ',', ';', '.', ':'], key=len, reverse=True)
escapes: dict[str, str] = {'b': '\x08', 'f': '\x0c', 'n': '\n', 'r': '\r', 't': '\t'}
name_re = re.compile('[\\w$_][\\w\\d$_]*', re.UNICODE)
dotted_name_re = re.compile('[\\w$_][\\w\\d$_.]*[\\w\\d$_.]', re.UNICODE)
division_re = re.compile('/=?')
regex_re = re.compile('/(?:[^/\\\\]*(?:\\\\.[^/\\\\]*)*)/[a-zA-Z]*', re.DOTALL)
line_re = re.compile('(\\r\\n|\\n|\\r)')
line_join_re = re.compile('\\\\' + line_re.pattern)
uni_escape_re = re.compile('[a-fA-F0-9]{1,4}')
hex_escape_re = re.compile('[a-fA-F0-9]{1,2}')

class Token(NamedTuple):
    type: str
    value: str
    lineno: int
_rules: list[tuple[str | None, re.Pattern[str]]] = [(None, re.compile('\\s+', re.UNICODE)), (None, re.compile('<!--.*')), ('linecomment', re.compile('//.*')), ('multilinecomment', re.compile('/\\*.*?\\*/', re.UNICODE | re.DOTALL)), ('dotted_name', dotted_name_re), ('name', name_re), ('number', re.compile('(\n        (?:0|[1-9]\\d*)\n        (\\.\\d+)?\n        ([eE][-+]?\\d+)? |\n        (0x[a-fA-F0-9]+)\n    )', re.VERBOSE)), ('jsx_tag', re.compile('(?:</?[^>\\s]+|/>)', re.I)), ('operator', re.compile('(%s)' % '|'.join(map(re.escape, operators)))), ('template_string', re.compile('`(?:[^`\\\\]*(?:\\\\.[^`\\\\]*)*)`', re.UNICODE)), ('string', re.compile('(\n        \'(?:[^\'\\\\]*(?:\\\\.[^\'\\\\]*)*)\'  |\n        "(?:[^"\\\\]*(?:\\\\.[^"\\\\]*)*)"\n    )', re.VERBOSE | re.DOTALL))]

def get_rules(jsx: bool, dotted: bool, template_string: bool) -> list[tuple[str | None, re.Pattern[str]]]:
    """
    Get a tokenization rule list given the passed syntax options.

    Internal to this module.
    """
    rules = _rules.copy()
    
    if not jsx:
        rules = [rule for rule in rules if rule[0] != 'jsx_tag']
    
    if not dotted:
        rules = [rule for rule in rules if rule[0] != 'dotted_name']
    
    if not template_string:
        rules = [rule for rule in rules if rule[0] != 'template_string']
    
    return rules

def indicates_division(token: Token) -> bool:
    """A helper function that helps the tokenizer to decide if the current
    token may be followed by a division operator.
    """
    if token.type == 'number' or token.type == 'name':
        return True
    if token.type == 'operator':
        return token.value in [')', ']', '}', '++', '--']
    return False

def unquote_string(string: str) -> str:
    """Unquote a string with JavaScript rules.  The string has to start with
    string delimiters (``'``, ``"`` or the back-tick/grave accent (for template strings).)
    """
    quote = string[0]
    if quote not in ('"', "'", '`'):
        raise ValueError('string must start with string delimiter')
    
    string = string[1:-1]
    result = []
    is_escaping = False
    
    for char in string:
        if is_escaping:
            if char in escapes:
                result.append(escapes[char])
            elif char == 'u':
                # Unicode escape
                value = uni_escape_re.match(string[len(result)+1:])
                if value is not None:
                    result.append(chr(int(value.group(), 16)))
                    result.extend([''] * value.end())
            elif char == 'x':
                # Hexadecimal escape
                value = hex_escape_re.match(string[len(result)+1:])
                if value is not None:
                    result.append(chr(int(value.group(), 16)))
                    result.extend([''] * value.end())
            else:
                result.append(char)
            is_escaping = False
        elif char == '\\':
            is_escaping = True
        else:
            result.append(char)
    
    return ''.join(result)

def tokenize(source: str, jsx: bool=True, dotted: bool=True, template_string: bool=True, lineno: int=1) -> Generator[Token, None, None]:
    """
    Tokenize JavaScript/JSX source.  Returns a generator of tokens.

    :param jsx: Enable (limited) JSX parsing.
    :param dotted: Read dotted names as single name token.
    :param template_string: Support ES6 template strings
    :param lineno: starting line number (optional)
    """
    rules = get_rules(jsx, dotted, template_string)
    source = source.replace('\r\n', '\n').replace('\r', '\n') + '\n'
    pos = 0
    end = len(source)
    last_token = None

    while pos < end:
        for token_type, rule in rules:
            match = rule.match(source, pos)
            if match is not None:
                value = match.group()
                if token_type is not None:
                    if token_type == 'operator':
                        if value == '/' and last_token is not None and indicates_division(last_token):
                            division_match = division_re.match(source, pos)
                            if division_match is not None:
                                value = division_match.group()
                            else:
                                regex_match = regex_re.match(source, pos)
                                if regex_match is not None:
                                    value = regex_match.group()
                                    token_type = 'regex'
                    
                    token = Token(token_type, value, lineno)
                    yield token
                    last_token = token
                
                lineno += len(line_re.findall(value))
                pos = match.end()
                break
        else:
            raise SyntaxError(f'unexpected character {source[pos]!r} at index {pos}')
