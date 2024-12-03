"""
    babel.messages.plurals
    ~~~~~~~~~~~~~~~~~~~~~~

    Plural form definitions.

    :copyright: (c) 2013-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import annotations
from operator import itemgetter
from babel.core import Locale, default_locale
LC_CTYPE: str | None = default_locale('LC_CTYPE')
PLURALS: dict[str, tuple[int, str]] = {'af': (2, '(n != 1)'), 'ar': (6, '(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=0 && n%100<=2 ? 4 : 5)'), 'be': (3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'), 'bg': (2, '(n != 1)'), 'bn': (2, '(n != 1)'), 'bo': (1, '0'), 'br': (6, '(n==1 ? 0 : n%10==1 && n%100!=11 && n%100!=71 && n%100!=91 ? 1 : n%10==2 && n%100!=12 && n%100!=72 && n%100!=92 ? 2 : (n%10==3 || n%10==4 || n%10==9) && n%100!=13 && n%100!=14 && n%100!=19 && n%100!=73 && n%100!=74 && n%100!=79 && n%100!=93 && n%100!=94 && n%100!=99 ? 3 : n%1000000==0 ? 4 : 5)'), 'bs': (3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'), 'ca': (2, '(n != 1)'), 'cs': (3, '((n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2)'), 'cv': (1, '0'), 'cy': (5, '(n==1 ? 1 : n==2 ? 2 : n==3 ? 3 : n==6 ? 4 : 0)'), 'da': (2, '(n != 1)'), 'de': (2, '(n != 1)'), 'dz': (1, '0'), 'el': (2, '(n != 1)'), 'en': (2, '(n != 1)'), 'eo': (2, '(n != 1)'), 'es': (2, '(n != 1)'), 'et': (2, '(n != 1)'), 'eu': (2, '(n != 1)'), 'fa': (1, '0'), 'fi': (2, '(n != 1)'), 'fr': (2, '(n > 1)'), 'fur': (2, '(n > 1)'), 'ga': (5, '(n==1 ? 0 : n==2 ? 1 : n>=3 && n<=6 ? 2 : n>=7 && n<=10 ? 3 : 4)'), 'gl': (2, '(n != 1)'), 'ha': (2, '(n != 1)'), 'he': (2, '(n != 1)'), 'hi': (2, '(n != 1)'), 'hr': (3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'), 'hu': (1, '0'), 'hy': (1, '0'), 'is': (2, '(n%10==1 && n%100!=11 ? 0 : 1)'), 'it': (2, '(n != 1)'), 'ja': (1, '0'), 'ka': (1, '0'), 'kg': (2, '(n != 1)'), 'km': (1, '0'), 'ko': (1, '0'), 'ku': (2, '(n != 1)'), 'lo': (1, '0'), 'lt': (3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && (n%100<10 || n%100>=20) ? 1 : 2)'), 'lv': (3, '(n%10==1 && n%100!=11 ? 0 : n != 0 ? 1 : 2)'), 'mt': (4, '(n==1 ? 0 : n==0 || ( n%100>=1 && n%100<=10) ? 1 : (n%100>10 && n%100<20 ) ? 2 : 3)'), 'nb': (2, '(n != 1)'), 'nl': (2, '(n != 1)'), 'nn': (2, '(n != 1)'), 'no': (2, '(n != 1)'), 'pa': (2, '(n != 1)'), 'pl': (3, '(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'), 'pt': (2, '(n != 1)'), 'pt_BR': (2, '(n > 1)'), 'ro': (3, '(n==1 ? 0 : (n==0 || (n%100 > 0 && n%100 < 20)) ? 1 : 2)'), 'ru': (3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'), 'sk': (3, '((n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2)'), 'sl': (4, '(n%100==1 ? 0 : n%100==2 ? 1 : n%100==3 || n%100==4 ? 2 : 3)'), 'sr': (3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'), 'st': (2, '(n != 1)'), 'sv': (2, '(n != 1)'), 'th': (1, '0'), 'tr': (1, '0'), 'uk': (3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'), 've': (2, '(n != 1)'), 'vi': (1, '0'), 'xh': (2, '(n != 1)'), 'zh': (1, '0')}
DEFAULT_PLURAL: tuple[int, str] = (2, '(n != 1)')

class _PluralTuple(tuple):
    """A tuple with plural information."""
    __slots__ = ()
    num_plurals = property(itemgetter(0), doc='\n    The number of plurals used by the locale.')
    plural_expr = property(itemgetter(1), doc='\n    The plural expression used by the locale.')
    plural_forms = property(lambda x: 'nplurals={}; plural={};'.format(*x), doc='\n    The plural expression used by the catalog or locale.')

    def __str__(self) -> str:
        return self.plural_forms

def get_plural(locale: str | None=LC_CTYPE) -> _PluralTuple:
    """A tuple with the information catalogs need to perform proper
    pluralization.  The first item of the tuple is the number of plural
    forms, the second the plural expression.

    >>> get_plural(locale='en')
    (2, '(n != 1)')
    >>> get_plural(locale='ga')
    (5, '(n==1 ? 0 : n==2 ? 1 : n>=3 && n<=6 ? 2 : n>=7 && n<=10 ? 3 : 4)')

    The object returned is a special tuple with additional members:

    >>> tup = get_plural("ja")
    >>> tup.num_plurals
    1
    >>> tup.plural_expr
    '0'
    >>> tup.plural_forms
    'nplurals=1; plural=0;'

    Converting the tuple into a string prints the plural forms for a
    gettext catalog:

    >>> str(tup)
    'nplurals=1; plural=0;'
    """
    if locale is None:
        locale = LC_CTYPE
    
    # Normalize the locale string
    locale = str(locale).replace('-', '_')
    
    # Try to get the plural rule for the given locale
    plural_rule = PLURALS.get(locale, DEFAULT_PLURAL)
    
    return _PluralTuple(plural_rule)
