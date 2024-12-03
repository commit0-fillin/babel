"""
    babel.lists
    ~~~~~~~~~~~

    Locale dependent formatting of lists.

    The default locale for the functions in this module is determined by the
    following environment variables, in that order:

     * ``LC_ALL``, and
     * ``LANG``

    :copyright: (c) 2015-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import annotations
from collections.abc import Sequence
from typing import TYPE_CHECKING
from babel.core import Locale, default_locale
if TYPE_CHECKING:
    from typing_extensions import Literal
DEFAULT_LOCALE = default_locale()

def format_list(lst: Sequence[str], style: Literal['standard', 'standard-short', 'or', 'or-short', 'unit', 'unit-short', 'unit-narrow']='standard', locale: Locale | str | None=DEFAULT_LOCALE) -> str:
    """
    Format the items in `lst` as a list.

    >>> format_list(['apples', 'oranges', 'pears'], locale='en')
    u'apples, oranges, and pears'
    >>> format_list(['apples', 'oranges', 'pears'], locale='zh')
    u'apples、oranges和pears'
    >>> format_list(['omena', 'peruna', 'aplari'], style='or', locale='fi')
    u'omena, peruna tai aplari'

    These styles are defined, but not all are necessarily available in all locales.
    The following text is verbatim from the Unicode TR35-49 spec [1].

    * standard:
      A typical 'and' list for arbitrary placeholders.
      eg. "January, February, and March"
    * standard-short:
      A short version of an 'and' list, suitable for use with short or abbreviated placeholder values.
      eg. "Jan., Feb., and Mar."
    * or:
      A typical 'or' list for arbitrary placeholders.
      eg. "January, February, or March"
    * or-short:
      A short version of an 'or' list.
      eg. "Jan., Feb., or Mar."
    * unit:
      A list suitable for wide units.
      eg. "3 feet, 7 inches"
    * unit-short:
      A list suitable for short units
      eg. "3 ft, 7 in"
    * unit-narrow:
      A list suitable for narrow units, where space on the screen is very limited.
      eg. "3′ 7″"

    [1]: https://www.unicode.org/reports/tr35/tr35-49/tr35-general.html#ListPatterns

    :param lst: a sequence of items to format in to a list
    :param style: the style to format the list with. See above for description.
    :param locale: the locale
    """
    if not lst:
        return ""
    
    if isinstance(locale, str):
        locale = Locale.parse(locale)
    elif locale is None:
        locale = Locale.parse(DEFAULT_LOCALE)

    list_patterns = locale.list_patterns.get(style, locale.list_patterns['standard'])
    
    if len(lst) == 1:
        return lst[0]
    elif len(lst) == 2:
        return list_patterns['2'].format(lst[0], lst[1])
    
    result = list_patterns['start'].format(lst[0], lst[1])
    for item in lst[2:-1]:
        result = list_patterns['middle'].format(result, item)
    return list_patterns['end'].format(result, lst[-1])
