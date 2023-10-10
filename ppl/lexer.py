"""词法分析器。"""

from __future__ import annotations

__docformat__ = 'google'

import enum
import re
import string
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import NamedTuple


class Symbol(int):
    """单个符号。"""

    @classmethod
    def from_letter(cls, letter: str) -> Symbol:
        """返回给定字母的对应符号。

        Args:
            letter: 一个字母。

        Returns:
            给定字母的对应符号。

        Raises:
            ValueError: 如果给定的字符串不是单个字符，或者不是字母。
        """
        if len(letter) != 1:
            raise ValueError('给定的字符串不是单个字符')
        if not letter.isalpha():
            raise ValueError('给定的字符不是字母')
        return Symbol(string.ascii_uppercase.find(letter.upper()))

    def __str__(self) -> str:
        return string.ascii_uppercase[self]

    def __repr__(self) -> str:
        return f'Symbol({int(self)!r})'


class OperatorSpec(NamedTuple):
    """表示某个运算符的详细细节。

    Attributes:
        input_form: 此运算符在输入时的呈现形式。
        actual_form: 此运算符在输出时的呈现形式。
        priority: 此运算符的优先级，越大越靠前。
    """

    input_form: str
    actual_form: str
    priority: int


class Operator(enum.Enum):
    """包含所有运算符的枚举。"""

    NEG = OperatorSpec('!', '¬', 100)
    CONJ = OperatorSpec('&', '∧', 90)
    DISJ = OperatorSpec('|', '∨', 80)
    MAT_COND = OperatorSpec('~', '→', 70)
    BICOND = OperatorSpec('=', '↔', 60)

    @classmethod
    def from_input_form(cls, form: str) -> Operator:
        """返回给定的输入形式所对应的运算符。

        Args:
            form: 一个有效的输入形式。

        Returns:
            对应的运算符。

        Raises:
            ValueError: 如果输入形式没有对应的运算符。
        """
        for op in cls:
            if op.value.input_form == form:
                return op
        raise ValueError(f'输入形式 {form!r} 没有对应的运算符')

    def __repr__(self) -> str:
        return f'Operator.{self.name}'


@dataclass
class AbstractToken[T]:
    """所有标志类的抽象基类。

    Attributes:
        value: 此标志的值。
        position: 此标志在输入字符串中所处的位置，以 0 起始。"""

    value: T
    position: int = field(repr=False)


class SymbolToken(AbstractToken[Symbol]):
    """表示单个符号的标志类。此类的 value 属性是标志所表示的符号。"""


class OperatorToken(AbstractToken[Operator]):
    """表示运算符的标志类。此类的 value 属性是标志所表示的运算符。"""


class AbstractParenToken(AbstractToken[None]):
    """表示括号的抽象标志类。"""


class LeftParenToken(AbstractParenToken):
    """表示左括号的标志类。"""


class RightParenToken(AbstractParenToken):
    """表示右括号的标志类。"""


class LexicalAnalysisFailedError(Exception):
    """词法分析发生错误。"""


def get_all_tokens(input_str: str) -> Generator[AbstractToken, None, None]:
    """获取给定输入字符串内的所有标志。

    Args:
        input_str: 输入字符串。

    Yields:
        每个获取的标志。
    """
    def create_token_spec() -> list[tuple[str, str]]:
        op_pattern = '|'.join(re.escape(o.value.input_form) for o in Operator)
        return [
            ('SYMBOL', r'[A-Za-z]'),
            ('OPERATOR', op_pattern),
            ('PAREN', r'[()]'),
            ('SKIP', r'\s+'),
            ('MISMATCH', r'.'),
        ]

    pattern = re.compile(
        '|'.join(f'(?P<{p[0]}>{p[1]})' for p in create_token_spec()))
    for mat in pattern.finditer(input_str):
        match mat.lastgroup:
            case 'SYMBOL':
                yield SymbolToken(Symbol.from_letter(mat.group()), mat.start())
            case 'OPERATOR':
                try:
                    op = Operator.from_input_form(mat.group())
                except ValueError:
                    raise RuntimeError
                yield OperatorToken(op, mat.start())
            case 'PAREN':
                match mat.group():
                    case '(':
                        yield LeftParenToken(None, mat.start())
                    case ')':
                        yield RightParenToken(None, mat.start())
                    case _:
                        raise RuntimeError
            case 'SKIP':
                pass
            case 'MISMATCH':
                raise LexicalAnalysisFailedError(
                    f'词法分析发生错误: 位于 {mat.start() + 1} 的 {mat.group()!r}')
            case _:
                raise RuntimeError


if __name__ == '__main__':
    import pprint
    while True:
        try:
            input_str = input('? ')
        except EOFError:
            break
        try:
            pprint.pprint(list(get_all_tokens(input_str)))
        except LexicalAnalysisFailedError as e:
            print(e)
