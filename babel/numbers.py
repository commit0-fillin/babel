"""
    babel.numbers
    ~~~~~~~~~~~~~

    Locale dependent formatting and parsing of numeric data.

    The default locale for the functions in this module is determined by the
    following environment variables, in that order:

     * ``LC_NUMERIC``,
     * ``LC_ALL``, and
     * ``LANG``

    :copyright: (c) 2013-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import annotations
import datetime
import decimal
import re
import warnings
from typing import TYPE_CHECKING, Any, cast, overload
from babel.core import Locale, default_locale, get_global
from babel.localedata import LocaleDataDict
if TYPE_CHECKING:
    from typing_extensions import Literal
LC_NUMERIC = default_locale('LC_NUMERIC')

class UnknownCurrencyError(Exception):
    """Exception thrown when a currency is requested for which no data is available.
    """

    def __init__(self, identifier: str) -> None:
        """Create the exception.
        :param identifier: the identifier string of the unsupported currency
        """
        Exception.__init__(self, f'Unknown currency {identifier!r}.')
        self.identifier = identifier

def list_currencies(locale: Locale | str | None=None) -> set[str]:
    """ Return a `set` of normalized currency codes.

    .. versionadded:: 2.5.0

    :param locale: filters returned currency codes by the provided locale.
                   Expected to be a locale instance or code. If no locale is
                   provided, returns the list of all currencies from all
                   locales.
    """
    if locale is None:
        return set(get_global('currency_fractions').keys())
    
    if isinstance(locale, str):
        locale = Locale.parse(locale)
    
    territory = locale.territory
    currencies = get_global('territory_currencies')
    
    if territory in currencies:
        return set(currency for currency, _ in currencies[territory])
    
    return set()

def validate_currency(currency: str, locale: Locale | str | None=None) -> None:
    """ Check the currency code is recognized by Babel.

    Accepts a ``locale`` parameter for fined-grained validation, working as
    the one defined above in ``list_currencies()`` method.

    Raises a `UnknownCurrencyError` exception if the currency is unknown to Babel.
    """
    if currency not in list_currencies(locale):
        raise UnknownCurrencyError(currency)

def is_currency(currency: str, locale: Locale | str | None=None) -> bool:
    """ Returns `True` only if a currency is recognized by Babel.

    This method always return a Boolean and never raise.
    """
    try:
        validate_currency(currency, locale)
        return True
    except UnknownCurrencyError:
        return False

def normalize_currency(currency: str, locale: Locale | str | None=None) -> str | None:
    """Returns the normalized identifier of any currency code.

    Accepts a ``locale`` parameter for fined-grained validation, working as
    the one defined above in ``list_currencies()`` method.

    Returns None if the currency is unknown to Babel.
    """
    currency = currency.upper()
    if is_currency(currency, locale):
        return currency
    return None

def get_currency_name(currency: str, count: float | decimal.Decimal | None=None, locale: Locale | str | None=LC_NUMERIC) -> str:
    """Return the name used by the locale for the specified currency.

    >>> get_currency_name('USD', locale='en_US')
    u'US Dollar'

    .. versionadded:: 0.9.4

    :param currency: the currency code.
    :param count: the optional count.  If provided the currency name
                  will be pluralized to that number if possible.
    :param locale: the `Locale` object or locale identifier.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if count is not None:
        plural_form = locale.plural_form(count)
    else:
        plural_form = 'other'

    currency_names = locale.currencies.get(currency)
    if currency_names:
        return currency_names.get(plural_form) or currency_names.get('other')
    return currency

def get_currency_symbol(currency: str, locale: Locale | str | None=LC_NUMERIC) -> str:
    """Return the symbol used by the locale for the specified currency.

    >>> get_currency_symbol('USD', locale='en_US')
    u'$'

    :param currency: the currency code.
    :param locale: the `Locale` object or locale identifier.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    return locale.currency_symbols.get(currency, currency)

def get_currency_precision(currency: str) -> int:
    """Return currency's precision.

    Precision is the number of decimals found after the decimal point in the
    currency's format pattern.

    .. versionadded:: 2.5.0

    :param currency: the currency code.
    """
    return get_global('currency_fractions').get(currency, {}).get('digits', 2)

def get_currency_unit_pattern(currency: str, count: float | decimal.Decimal | None=None, locale: Locale | str | None=LC_NUMERIC) -> str:
    """
    Return the unit pattern used for long display of a currency value
    for a given locale.
    This is a string containing ``{0}`` where the numeric part
    should be substituted and ``{1}`` where the currency long display
    name should be substituted.

    >>> get_currency_unit_pattern('USD', locale='en_US', count=10)
    u'{0} {1}'

    .. versionadded:: 2.7.0

    :param currency: the currency code.
    :param count: the optional count.  If provided the unit
                  pattern for that number will be returned.
    :param locale: the `Locale` object or locale identifier.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if count is not None:
        plural_form = locale.plural_form(count)
    else:
        plural_form = 'other'

    patterns = locale.currency_formats.get('unit_patterns', {})
    return patterns.get(plural_form, '{0} {1}')

def get_territory_currencies(territory: str, start_date: datetime.date | None=None, end_date: datetime.date | None=None, tender: bool=True, non_tender: bool=False, include_details: bool=False) -> list[str] | list[dict[str, Any]]:
    """Returns the list of currencies for the given territory that are valid for
    the given date range.  In addition to that the currency database
    distinguishes between tender and non-tender currencies.  By default only
    tender currencies are returned.

    The return value is a list of all currencies roughly ordered by the time
    of when the currency became active.  The longer the currency is being in
    use the more to the left of the list it will be.

    The start date defaults to today.  If no end date is given it will be the
    same as the start date.  Otherwise a range can be defined.  For instance
    this can be used to find the currencies in use in Austria between 1995 and
    2011:

    >>> from datetime import date
    >>> get_territory_currencies('AT', date(1995, 1, 1), date(2011, 1, 1))
    ['ATS', 'EUR']

    Likewise it's also possible to find all the currencies in use on a
    single date:

    >>> get_territory_currencies('AT', date(1995, 1, 1))
    ['ATS']
    >>> get_territory_currencies('AT', date(2011, 1, 1))
    ['EUR']

    By default the return value only includes tender currencies.  This
    however can be changed:

    >>> get_territory_currencies('US')
    ['USD']
    >>> get_territory_currencies('US', tender=False, non_tender=True,
    ...                          start_date=date(2014, 1, 1))
    ['USN', 'USS']

    .. versionadded:: 2.0

    :param territory: the name of the territory to find the currency for.
    :param start_date: the start date.  If not given today is assumed.
    :param end_date: the end date.  If not given the start date is assumed.
    :param tender: controls whether tender currencies should be included.
    :param non_tender: controls whether non-tender currencies should be
                       included.
    :param include_details: if set to `True`, instead of returning currency
                            codes the return value will be dictionaries
                            with detail information.  In that case each
                            dictionary will have the keys ``'currency'``,
                            ``'from'``, ``'to'``, and ``'tender'``.
    """
    if start_date is None:
        start_date = datetime.date.today()
    if end_date is None:
        end_date = start_date

    currencies = get_global('territory_currencies').get(territory, [])
    result = []

    for currency_info in currencies:
        currency = currency_info['currency']
        from_date = currency_info.get('from')
        to_date = currency_info.get('to')
        is_tender = currency_info.get('tender', True)

        if from_date and from_date > end_date:
            continue
        if to_date and to_date < start_date:
            continue
        if is_tender and not tender:
            continue
        if not is_tender and not non_tender:
            continue

        if include_details:
            result.append({
                'currency': currency,
                'from': from_date,
                'to': to_date,
                'tender': is_tender
            })
        else:
            result.append(currency)

    return result

class UnsupportedNumberingSystemError(Exception):
    """Exception thrown when an unsupported numbering system is requested for the given Locale."""
    pass

def get_decimal_symbol(locale: Locale | str | None=LC_NUMERIC, *, numbering_system: Literal['default'] | str='latn') -> str:
    """Return the symbol used by the locale to separate decimal fractions.

    >>> get_decimal_symbol('en_US')
    u'.'
    >>> get_decimal_symbol('ar_EG', numbering_system='default')
    u'٫'
    >>> get_decimal_symbol('ar_EG', numbering_system='latn')
    u'.'

    :param locale: the `Locale` object or locale identifier
    :param numbering_system: The numbering system used for fetching the symbol. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: If the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if numbering_system == 'default':
        numbering_system = locale.default_numbering_system

    try:
        return locale.number_symbols[numbering_system]['decimal']
    except KeyError:
        raise UnsupportedNumberingSystemError(f"Numbering system '{numbering_system}' is not supported for locale '{locale}'")

def get_plus_sign_symbol(locale: Locale | str | None=LC_NUMERIC, *, numbering_system: Literal['default'] | str='latn') -> str:
    """Return the plus sign symbol used by the current locale.

    >>> get_plus_sign_symbol('en_US')
    u'+'
    >>> get_plus_sign_symbol('ar_EG', numbering_system='default')
    u'\u061c+'
    >>> get_plus_sign_symbol('ar_EG', numbering_system='latn')
    u'\u200e+'

    :param locale: the `Locale` object or locale identifier
    :param numbering_system: The numbering system used for fetching the symbol. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: if the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if numbering_system == 'default':
        numbering_system = locale.default_numbering_system

    try:
        return locale.number_symbols[numbering_system]['plusSign']
    except KeyError:
        raise UnsupportedNumberingSystemError(f"Numbering system '{numbering_system}' is not supported for locale '{locale}'")

def get_minus_sign_symbol(locale: Locale | str | None=LC_NUMERIC, *, numbering_system: Literal['default'] | str='latn') -> str:
    """Return the minus sign symbol used by the current locale.

    >>> get_minus_sign_symbol('en_US')
    u'-'
    >>> get_minus_sign_symbol('ar_EG', numbering_system='default')
    u'\u061c-'
    >>> get_minus_sign_symbol('ar_EG', numbering_system='latn')
    u'\u200e-'

    :param locale: the `Locale` object or locale identifier
    :param numbering_system: The numbering system used for fetching the symbol. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: if the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if numbering_system == 'default':
        numbering_system = locale.default_numbering_system

    try:
        return locale.number_symbols[numbering_system]['minusSign']
    except KeyError:
        raise UnsupportedNumberingSystemError(f"Numbering system '{numbering_system}' is not supported for locale '{locale}'")

def get_exponential_symbol(locale: Locale | str | None=LC_NUMERIC, *, numbering_system: Literal['default'] | str='latn') -> str:
    """Return the symbol used by the locale to separate mantissa and exponent.

    >>> get_exponential_symbol('en_US')
    u'E'
    >>> get_exponential_symbol('ar_EG', numbering_system='default')
    u'اس'
    >>> get_exponential_symbol('ar_EG', numbering_system='latn')
    u'E'

    :param locale: the `Locale` object or locale identifier
    :param numbering_system: The numbering system used for fetching the symbol. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: if the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if numbering_system == 'default':
        numbering_system = locale.default_numbering_system

    try:
        return locale.number_symbols[numbering_system]['exponential']
    except KeyError:
        raise UnsupportedNumberingSystemError(f"Numbering system '{numbering_system}' is not supported for locale '{locale}'")

def get_group_symbol(locale: Locale | str | None=LC_NUMERIC, *, numbering_system: Literal['default'] | str='latn') -> str:
    """Return the symbol used by the locale to separate groups of thousands.

    >>> get_group_symbol('en_US')
    u','
    >>> get_group_symbol('ar_EG', numbering_system='default')
    u'٬'
    >>> get_group_symbol('ar_EG', numbering_system='latn')
    u','

    :param locale: the `Locale` object or locale identifier
    :param numbering_system: The numbering system used for fetching the symbol. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: if the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if numbering_system == 'default':
        numbering_system = locale.default_numbering_system

    try:
        return locale.number_symbols[numbering_system]['group']
    except KeyError:
        raise UnsupportedNumberingSystemError(f"Numbering system '{numbering_system}' is not supported for locale '{locale}'")

def get_infinity_symbol(locale: Locale | str | None=LC_NUMERIC, *, numbering_system: Literal['default'] | str='latn') -> str:
    """Return the symbol used by the locale to represent infinity.

    >>> get_infinity_symbol('en_US')
    u'∞'
    >>> get_infinity_symbol('ar_EG', numbering_system='default')
    u'∞'
    >>> get_infinity_symbol('ar_EG', numbering_system='latn')
    u'∞'

    :param locale: the `Locale` object or locale identifier
    :param numbering_system: The numbering system used for fetching the symbol. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: if the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if numbering_system == 'default':
        numbering_system = locale.default_numbering_system

    try:
        return locale.number_symbols[numbering_system]['infinity']
    except KeyError:
        raise UnsupportedNumberingSystemError(f"Numbering system '{numbering_system}' is not supported for locale '{locale}'")

def format_number(number: float | decimal.Decimal | str, locale: Locale | str | None=LC_NUMERIC) -> str:
    """Return the given number formatted for a specific locale.

    >>> format_number(1099, locale='en_US')  # doctest: +SKIP
    u'1,099'
    >>> format_number(1099, locale='de_DE')  # doctest: +SKIP
    u'1.099'

    .. deprecated:: 2.6.0

       Use babel.numbers.format_decimal() instead.

    :param number: the number to format
    :param locale: the `Locale` object or locale identifier


    """
    warnings.warn("Use babel.numbers.format_decimal() instead.", DeprecationWarning, stacklevel=2)
    return format_decimal(number, locale=locale)

def get_decimal_precision(number: decimal.Decimal) -> int:
    """Return maximum precision of a decimal instance's fractional part.

    Precision is extracted from the fractional part only.
    """
    return -number.as_tuple().exponent

def get_decimal_quantum(precision: int | decimal.Decimal) -> decimal.Decimal:
    """Return minimal quantum of a number, as defined by precision."""
    if isinstance(precision, decimal.Decimal):
        return precision.normalize().as_tuple().exponent
    return decimal.Decimal('0.1') ** precision

def format_decimal(number: float | decimal.Decimal | str, format: str | NumberPattern | None=None, locale: Locale | str | None=LC_NUMERIC, decimal_quantization: bool=True, group_separator: bool=True, *, numbering_system: Literal['default'] | str='latn') -> str:
    """Return the given decimal number formatted for a specific locale.

    >>> format_decimal(1.2345, locale='en_US')
    u'1.234'
    >>> format_decimal(1.2346, locale='en_US')
    u'1.235'
    >>> format_decimal(-1.2346, locale='en_US')
    u'-1.235'
    >>> format_decimal(1.2345, locale='sv_SE')
    u'1,234'
    >>> format_decimal(1.2345, locale='de')
    u'1,234'
    >>> format_decimal(1.2345, locale='ar_EG', numbering_system='default')
    u'1٫234'
    >>> format_decimal(1.2345, locale='ar_EG', numbering_system='latn')
    u'1.234'

    The appropriate thousands grouping and the decimal separator are used for
    each locale:

    >>> format_decimal(12345.5, locale='en_US')
    u'12,345.5'

    By default the locale is allowed to truncate and round a high-precision
    number by forcing its format pattern onto the decimal part. You can bypass
    this behavior with the `decimal_quantization` parameter:

    >>> format_decimal(1.2346, locale='en_US')
    u'1.235'
    >>> format_decimal(1.2346, locale='en_US', decimal_quantization=False)
    u'1.2346'
    >>> format_decimal(12345.67, locale='fr_CA', group_separator=False)
    u'12345,67'
    >>> format_decimal(12345.67, locale='en_US', group_separator=True)
    u'12,345.67'

    :param number: the number to format
    :param format:
    :param locale: the `Locale` object or locale identifier
    :param decimal_quantization: Truncate and round high-precision numbers to
                                 the format pattern. Defaults to `True`.
    :param group_separator: Boolean to switch group separator on/off in a locale's
                            number format.
    :param numbering_system: The numbering system used for formatting number symbols. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: If the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if isinstance(number, str):
        number = decimal.Decimal(number)
    
    if format is None:
        format = locale.decimal_formats[None]
    if isinstance(format, str):
        format = parse_pattern(format)

    if numbering_system == 'default':
        numbering_system = locale.default_numbering_system

    try:
        symbols = locale.number_symbols[numbering_system]
    except KeyError:
        raise UnsupportedNumberingSystemError(f"Numbering system '{numbering_system}' is not supported for locale '{locale}'")

    return format.apply(number, locale, decimal_quantization=decimal_quantization, group_separator=group_separator, symbols=symbols)

def format_compact_decimal(number: float | decimal.Decimal | str, *, format_type: Literal['short', 'long']='short', locale: Locale | str | None=LC_NUMERIC, fraction_digits: int=0, numbering_system: Literal['default'] | str='latn') -> str:
    """Return the given decimal number formatted for a specific locale in compact form.

    >>> format_compact_decimal(12345, format_type="short", locale='en_US')
    u'12K'
    >>> format_compact_decimal(12345, format_type="long", locale='en_US')
    u'12 thousand'
    >>> format_compact_decimal(12345, format_type="short", locale='en_US', fraction_digits=2)
    u'12.34K'
    >>> format_compact_decimal(1234567, format_type="short", locale="ja_JP")
    u'123万'
    >>> format_compact_decimal(2345678, format_type="long", locale="mk")
    u'2 милиони'
    >>> format_compact_decimal(21000000, format_type="long", locale="mk")
    u'21 милион'
    >>> format_compact_decimal(12345, format_type="short", locale='ar_EG', fraction_digits=2, numbering_system='default')
    u'12٫34\xa0ألف'

    :param number: the number to format
    :param format_type: Compact format to use ("short" or "long")
    :param locale: the `Locale` object or locale identifier
    :param fraction_digits: Number of digits after the decimal point to use. Defaults to `0`.
    :param numbering_system: The numbering system used for formatting number symbols. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: If the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if isinstance(number, str):
        number = decimal.Decimal(number)

    compact_format = locale.compact_decimal_formats.get(format_type)
    if not compact_format:
        raise ValueError(f"Unsupported format type: {format_type}")

    magnitude, pattern = _get_compact_format(number, compact_format, locale, fraction_digits)
    if pattern is None:
        return format_decimal(number, locale=locale, numbering_system=numbering_system)

    formatted = pattern.apply(
        number / magnitude,
        locale,
        decimal_quantization=True,
        force_frac=(fraction_digits, fraction_digits),
        numbering_system=numbering_system
    )

    return formatted.strip()

def _get_compact_format(number: float | decimal.Decimal | str, compact_format: LocaleDataDict, locale: Locale, fraction_digits: int) -> tuple[decimal.Decimal, NumberPattern | None]:
    """Returns the number after dividing by the unit and the format pattern to use.
    The algorithm is described here:
    https://www.unicode.org/reports/tr35/tr35-45/tr35-numbers.html#Compact_Number_Formats.
    """
    if isinstance(number, str):
        number = decimal.Decimal(number)

    abs_number = abs(number)
    log10 = int(math.log10(abs_number)) if abs_number != 0 else 0
    magnitude = 10 ** max(0, log10)

    plural_form = locale.plural_form(abs_number)
    patterns = compact_format.get(plural_form, compact_format.get('other', {}))

    for threshold in sorted(patterns.keys(), key=lambda x: int(x), reverse=True):
        if abs_number >= int(threshold):
            pattern = patterns[threshold]
            if isinstance(pattern, str):
                pattern = parse_pattern(pattern)
            return decimal.Decimal(threshold), pattern

    return decimal.Decimal('1'), None

class UnknownCurrencyFormatError(KeyError):
    """Exception raised when an unknown currency format is requested."""

def format_currency(number: float | decimal.Decimal | str, currency: str, format: str | NumberPattern | None=None, locale: Locale | str | None=LC_NUMERIC, currency_digits: bool=True, format_type: Literal['name', 'standard', 'accounting']='standard', decimal_quantization: bool=True, group_separator: bool=True, *, numbering_system: Literal['default'] | str='latn') -> str:
    """Return formatted currency value.

    >>> format_currency(1099.98, 'USD', locale='en_US')
    '$1,099.98'
    >>> format_currency(1099.98, 'USD', locale='es_CO')
    u'US$1.099,98'
    >>> format_currency(1099.98, 'EUR', locale='de_DE')
    u'1.099,98\\xa0\\u20ac'
    >>> format_currency(1099.98, 'EGP', locale='ar_EG', numbering_system='default')
    u'\u200f1٬099٫98\xa0ج.م.\u200f'

    The format can also be specified explicitly.  The currency is
    placed with the '¤' sign.  As the sign gets repeated the format
    expands (¤ being the symbol, ¤¤ is the currency abbreviation and
    ¤¤¤ is the full name of the currency):

    >>> format_currency(1099.98, 'EUR', u'¤¤ #,##0.00', locale='en_US')
    u'EUR 1,099.98'
    >>> format_currency(1099.98, 'EUR', u'#,##0.00 ¤¤¤', locale='en_US')
    u'1,099.98 euros'

    Currencies usually have a specific number of decimal digits. This function
    favours that information over the given format:

    >>> format_currency(1099.98, 'JPY', locale='en_US')
    u'\\xa51,100'
    >>> format_currency(1099.98, 'COP', u'#,##0.00', locale='es_ES')
    u'1.099,98'

    However, the number of decimal digits can be overridden from the currency
    information, by setting the last parameter to ``False``:

    >>> format_currency(1099.98, 'JPY', locale='en_US', currency_digits=False)
    u'\\xa51,099.98'
    >>> format_currency(1099.98, 'COP', u'#,##0.00', locale='es_ES', currency_digits=False)
    u'1.099,98'

    If a format is not specified the type of currency format to use
    from the locale can be specified:

    >>> format_currency(1099.98, 'EUR', locale='en_US', format_type='standard')
    u'\\u20ac1,099.98'

    When the given currency format type is not available, an exception is
    raised:

    >>> format_currency('1099.98', 'EUR', locale='root', format_type='unknown')
    Traceback (most recent call last):
        ...
    UnknownCurrencyFormatError: "'unknown' is not a known currency format type"

    >>> format_currency(101299.98, 'USD', locale='en_US', group_separator=False)
    u'$101299.98'

    >>> format_currency(101299.98, 'USD', locale='en_US', group_separator=True)
    u'$101,299.98'

    You can also pass format_type='name' to use long display names. The order of
    the number and currency name, along with the correct localized plural form
    of the currency name, is chosen according to locale:

    >>> format_currency(1, 'USD', locale='en_US', format_type='name')
    u'1.00 US dollar'
    >>> format_currency(1099.98, 'USD', locale='en_US', format_type='name')
    u'1,099.98 US dollars'
    >>> format_currency(1099.98, 'USD', locale='ee', format_type='name')
    u'us ga dollar 1,099.98'

    By default the locale is allowed to truncate and round a high-precision
    number by forcing its format pattern onto the decimal part. You can bypass
    this behavior with the `decimal_quantization` parameter:

    >>> format_currency(1099.9876, 'USD', locale='en_US')
    u'$1,099.99'
    >>> format_currency(1099.9876, 'USD', locale='en_US', decimal_quantization=False)
    u'$1,099.9876'

    :param number: the number to format
    :param currency: the currency code
    :param format: the format string to use
    :param locale: the `Locale` object or locale identifier
    :param currency_digits: use the currency's natural number of decimal digits
    :param format_type: the currency format type to use
    :param decimal_quantization: Truncate and round high-precision numbers to
                                 the format pattern. Defaults to `True`.
    :param group_separator: Boolean to switch group separator on/off in a locale's
                            number format.
    :param numbering_system: The numbering system used for formatting number symbols. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: If the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if format_type == 'name':
        return _format_currency_long_name(number, currency, format, locale, currency_digits, decimal_quantization, group_separator, numbering_system)

    try:
        format = locale.currency_formats[format_type]
    except KeyError:
        raise UnknownCurrencyFormatError(f"'{format_type}' is not a known currency format type")

    pattern = parse_pattern(format)
    return pattern.apply(number, locale, currency=currency, currency_digits=currency_digits,
                         decimal_quantization=decimal_quantization, group_separator=group_separator,
                         numbering_system=numbering_system)

def _format_currency_long_name(number, currency, format, locale, currency_digits, decimal_quantization, group_separator, numbering_system):
    formatted_number = format_decimal(number, format=format, locale=locale, decimal_quantization=decimal_quantization,
                                      group_separator=group_separator, numbering_system=numbering_system)
    currency_name = get_currency_name(currency, count=number, locale=locale)
    pattern = locale.currency_formats.get('name_pattern', '{0} {1}')
    return pattern.format(formatted_number, currency_name)

def format_compact_currency(number: float | decimal.Decimal | str, currency: str, *, format_type: Literal['short']='short', locale: Locale | str | None=LC_NUMERIC, fraction_digits: int=0, numbering_system: Literal['default'] | str='latn') -> str:
    """Format a number as a currency value in compact form.

    >>> format_compact_currency(12345, 'USD', locale='en_US')
    u'$12K'
    >>> format_compact_currency(123456789, 'USD', locale='en_US', fraction_digits=2)
    u'$123.46M'
    >>> format_compact_currency(123456789, 'EUR', locale='de_DE', fraction_digits=1)
    '123,5\xa0Mio.\xa0€'

    :param number: the number to format
    :param currency: the currency code
    :param format_type: the compact format type to use. Defaults to "short".
    :param locale: the `Locale` object or locale identifier
    :param fraction_digits: Number of digits after the decimal point to use. Defaults to `0`.
    :param numbering_system: The numbering system used for formatting number symbols. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: If the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if isinstance(number, str):
        number = decimal.Decimal(number)

    compact_format = locale.compact_currency_formats.get(format_type)
    if not compact_format:
        raise ValueError(f"Unsupported format type: {format_type}")

    magnitude, pattern = _get_compact_format(number, compact_format, locale, fraction_digits)
    if pattern is None:
        return format_currency(number, currency, locale=locale, numbering_system=numbering_system)

    formatted = pattern.apply(
        number / magnitude,
        locale,
        currency=currency,
        decimal_quantization=True,
        force_frac=(fraction_digits, fraction_digits),
        numbering_system=numbering_system
    )

    return formatted.strip()

def format_percent(number: float | decimal.Decimal | str, format: str | NumberPattern | None=None, locale: Locale | str | None=LC_NUMERIC, decimal_quantization: bool=True, group_separator: bool=True, *, numbering_system: Literal['default'] | str='latn') -> str:
    """Return formatted percent value for a specific locale.

    >>> format_percent(0.34, locale='en_US')
    u'34%'
    >>> format_percent(25.1234, locale='en_US')
    u'2,512%'
    >>> format_percent(25.1234, locale='sv_SE')
    u'2\\xa0512\\xa0%'
    >>> format_percent(25.1234, locale='ar_EG', numbering_system='default')
    u'2٬512%'

    The format pattern can also be specified explicitly:

    >>> format_percent(25.1234, u'#,##0‰', locale='en_US')
    u'25,123‰'

    By default the locale is allowed to truncate and round a high-precision
    number by forcing its format pattern onto the decimal part. You can bypass
    this behavior with the `decimal_quantization` parameter:

    >>> format_percent(23.9876, locale='en_US')
    u'2,399%'
    >>> format_percent(23.9876, locale='en_US', decimal_quantization=False)
    u'2,398.76%'

    >>> format_percent(229291.1234, locale='pt_BR', group_separator=False)
    u'22929112%'

    >>> format_percent(229291.1234, locale='pt_BR', group_separator=True)
    u'22.929.112%'

    :param number: the percent number to format
    :param format:
    :param locale: the `Locale` object or locale identifier
    :param decimal_quantization: Truncate and round high-precision numbers to
                                 the format pattern. Defaults to `True`.
    :param group_separator: Boolean to switch group separator on/off in a locale's
                            number format.
    :param numbering_system: The numbering system used for formatting number symbols. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: If the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if format is None:
        format = locale.percent_formats[None]
    if isinstance(format, str):
        format = parse_pattern(format)

    pattern = format.pattern.replace('#', '#/100')
    custom_pattern = parse_pattern(pattern)

    return custom_pattern.apply(
        number,
        locale,
        decimal_quantization=decimal_quantization,
        group_separator=group_separator,
        numbering_system=numbering_system
    )

def format_scientific(number: float | decimal.Decimal | str, format: str | NumberPattern | None=None, locale: Locale | str | None=LC_NUMERIC, decimal_quantization: bool=True, *, numbering_system: Literal['default'] | str='latn') -> str:
    """Return value formatted in scientific notation for a specific locale.

    >>> format_scientific(10000, locale='en_US')
    u'1E4'
    >>> format_scientific(10000, locale='ar_EG', numbering_system='default')
    u'1اس4'

    The format pattern can also be specified explicitly:

    >>> format_scientific(1234567, u'##0.##E00', locale='en_US')
    u'1.23E06'

    By default the locale is allowed to truncate and round a high-precision
    number by forcing its format pattern onto the decimal part. You can bypass
    this behavior with the `decimal_quantization` parameter:

    >>> format_scientific(1234.9876, u'#.##E0', locale='en_US')
    u'1.23E3'
    >>> format_scientific(1234.9876, u'#.##E0', locale='en_US', decimal_quantization=False)
    u'1.2349876E3'

    :param number: the number to format
    :param format:
    :param locale: the `Locale` object or locale identifier
    :param decimal_quantization: Truncate and round high-precision numbers to
                                 the format pattern. Defaults to `True`.
    :param numbering_system: The numbering system used for formatting number symbols. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: If the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if format is None:
        format = locale.scientific_formats[None]
    if isinstance(format, str):
        format = parse_pattern(format)

    return format.apply(
        number,
        locale,
        decimal_quantization=decimal_quantization,
        numbering_system=numbering_system
    )

class NumberFormatError(ValueError):
    """Exception raised when a string cannot be parsed into a number."""

    def __init__(self, message: str, suggestions: list[str] | None=None) -> None:
        super().__init__(message)
        self.suggestions = suggestions

def parse_number(string: str, locale: Locale | str | None=LC_NUMERIC, *, numbering_system: Literal['default'] | str='latn') -> int:
    """Parse localized number string into an integer.

    >>> parse_number('1,099', locale='en_US')
    1099
    >>> parse_number('1.099', locale='de_DE')
    1099

    When the given string cannot be parsed, an exception is raised:

    >>> parse_number('1.099,98', locale='de')
    Traceback (most recent call last):
        ...
    NumberFormatError: '1.099,98' is not a valid number

    :param string: the string to parse
    :param locale: the `Locale` object or locale identifier
    :param numbering_system: The numbering system used for formatting number symbols. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :return: the parsed number
    :raise `NumberFormatError`: if the string can not be converted to a number
    :raise `UnsupportedNumberingSystemError`: if the numbering system is not supported by the locale.
    """
    try:
        return int(parse_decimal(string, locale, numbering_system=numbering_system))
    except ValueError:
        raise NumberFormatError(f"'{string}' is not a valid number")

def parse_decimal(string: str, locale: Locale | str | None=LC_NUMERIC, strict: bool=False, *, numbering_system: Literal['default'] | str='latn') -> decimal.Decimal:
    """Parse localized decimal string into a decimal.

    >>> parse_decimal('1,099.98', locale='en_US')
    Decimal('1099.98')
    >>> parse_decimal('1.099,98', locale='de')
    Decimal('1099.98')
    >>> parse_decimal('12 345,123', locale='ru')
    Decimal('12345.123')
    >>> parse_decimal('1٬099٫98', locale='ar_EG', numbering_system='default')
    Decimal('1099.98')

    When the given string cannot be parsed, an exception is raised:

    >>> parse_decimal('2,109,998', locale='de')
    Traceback (most recent call last):
        ...
    NumberFormatError: '2,109,998' is not a valid decimal number

    If `strict` is set to `True` and the given string contains a number
    formatted in an irregular way, an exception is raised:

    >>> parse_decimal('30.00', locale='de', strict=True)
    Traceback (most recent call last):
        ...
    NumberFormatError: '30.00' is not a properly formatted decimal number. Did you mean '3.000'? Or maybe '30,00'?

    >>> parse_decimal('0.00', locale='de', strict=True)
    Traceback (most recent call last):
        ...
    NumberFormatError: '0.00' is not a properly formatted decimal number. Did you mean '0'?

    :param string: the string to parse
    :param locale: the `Locale` object or locale identifier
    :param strict: controls whether numbers formatted in a weird way are
                   accepted or rejected
    :param numbering_system: The numbering system used for formatting number symbols. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise NumberFormatError: if the string can not be converted to a
                              decimal number
    :raise UnsupportedNumberingSystemError: if the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if numbering_system == 'default':
        numbering_system = locale.default_numbering_system

    try:
        symbols = locale.number_symbols[numbering_system]
    except KeyError:
        raise UnsupportedNumberingSystemError(f"Numbering system '{numbering_system}' is not supported for locale '{locale}'")

    group_symbol = symbols['group']
    decimal_symbol = symbols['decimal']

    # Remove group separators
    string = string.replace(group_symbol, '')

    # Replace decimal separator with a dot
    string = string.replace(decimal_symbol, '.')

    # Remove any whitespace
    string = string.strip()

    try:
        parsed = decimal.Decimal(string)
    except decimal.InvalidOperation:
        raise NumberFormatError(f"'{string}' is not a valid decimal number")

    if strict:
        # Check if the original string matches the expected format
        formatted = format_decimal(parsed, locale=locale, numbering_system=numbering_system)
        if formatted != string:
            suggestions = [
                format_decimal(parsed, locale=locale, numbering_system=numbering_system),
                format_decimal(parsed, locale=locale, numbering_system=numbering_system, decimal_quantization=False)
            ]
            raise NumberFormatError(f"'{string}' is not a properly formatted decimal number. Did you mean '{suggestions[0]}'? Or maybe '{suggestions[1]}'?")

    return parsed

def _remove_trailing_zeros_after_decimal(string: str, decimal_symbol: str) -> str:
    """
    Remove trailing zeros from the decimal part of a numeric string.

    This function takes a string representing a numeric value and a decimal symbol.
    It removes any trailing zeros that appear after the decimal symbol in the number.
    If the decimal part becomes empty after removing trailing zeros, the decimal symbol
    is also removed. If the string does not contain the decimal symbol, it is returned unchanged.

    :param string: The numeric string from which to remove trailing zeros.
    :type string: str
    :param decimal_symbol: The symbol used to denote the decimal point.
    :type decimal_symbol: str
    :return: The numeric string with trailing zeros removed from its decimal part.
    :rtype: str

    Example:
    >>> _remove_trailing_zeros_after_decimal("123.4500", ".")
    '123.45'
    >>> _remove_trailing_zeros_after_decimal("100.000", ".")
    '100'
    >>> _remove_trailing_zeros_after_decimal("100", ".")
    '100'
    """
    if decimal_symbol not in string:
        return string

    integer_part, _, decimal_part = string.partition(decimal_symbol)
    decimal_part = decimal_part.rstrip('0')

    if decimal_part:
        return f"{integer_part}{decimal_symbol}{decimal_part}"
    else:
        return integer_part
PREFIX_END = '[^0-9@#.,]'
NUMBER_TOKEN = '[0-9@#.,E+]'
PREFIX_PATTERN = "(?P<prefix>(?:'[^']*'|%s)*)" % PREFIX_END
NUMBER_PATTERN = '(?P<number>%s*)' % NUMBER_TOKEN
SUFFIX_PATTERN = '(?P<suffix>.*)'
number_re = re.compile(f'{PREFIX_PATTERN}{NUMBER_PATTERN}{SUFFIX_PATTERN}')

def parse_grouping(p: str) -> tuple[int, int]:
    """Parse primary and secondary digit grouping

    >>> parse_grouping('##')
    (1000, 1000)
    >>> parse_grouping('#,###')
    (3, 3)
    >>> parse_grouping('#,####,###')
    (3, 4)
    """
    width = len(p)
    g1 = p.rfind(',')
    if g1 == -1:
        return 1000, 1000
    g1 = width - g1 - 1
    g2 = p[:-g1 - 1].rfind(',')
    if g2 == -1:
        return g1, g1
    g2 = width - g1 - g2 - 2
    return g1, g2

def parse_pattern(pattern: NumberPattern | str) -> NumberPattern:
    """Parse number format patterns"""
    if isinstance(pattern, NumberPattern):
        return pattern

    # Parse the pattern string
    if ';' in pattern:
        positive, negative = pattern.split(';')
    else:
        positive = pattern
        negative = ''

    # Extract prefix and suffix
    def extract_affix(pattern):
        prefix = suffix = ''
        for part in number_re.split(pattern):
            if part and part.find('0') == -1 and part.find('#') == -1 and part.find(',') == -1 and part.find('.') == -1 and part.find('E') == -1:
                if prefix:
                    suffix = part
                else:
                    prefix = part
        return prefix, suffix

    pos_prefix, pos_suffix = extract_affix(positive)
    if negative:
        neg_prefix, neg_suffix = extract_affix(negative)
    else:
        neg_prefix = '-' + pos_prefix
        neg_suffix = pos_suffix

    # Extract number format
    number = number_re.search(positive).group('number')

    # Parse grouping
    if ',' in number:
        integer, _, fraction = number.partition('.')
        grouping = parse_grouping(integer)
    else:
        grouping = (1000, 1000)

    # Parse integer and fraction precision
    int_prec = fraction_prec = None
    if '.' in number:
        integer, fraction = number.split('.')
        int_prec = (len(integer.replace(',', '').replace('#', '')),
                    len(integer.replace(',', '')))
        fraction_prec = (len(fraction.replace('#', '')),
                         len(fraction))
    else:
        int_prec = (len(number.replace(',', '').replace('#', '')),
                    len(number.replace(',', '')))

    # Parse scientific notation
    exp_prec = None
    if 'E' in number:
        exp_part = number.split('E')[1]
        if '+' in exp_part:
            exp_plus = True
            exp_prec = len(exp_part) - 1
        else:
            exp_plus = False
            exp_prec = len(exp_part)
    else:
        exp_plus = None

    return NumberPattern(pattern, (pos_prefix, neg_prefix), (pos_suffix, neg_suffix),
                         grouping, int_prec, fraction_prec, exp_prec, exp_plus, number)

class NumberPattern:

    def __init__(self, pattern: str, prefix: tuple[str, str], suffix: tuple[str, str], grouping: tuple[int, int], int_prec: tuple[int, int], frac_prec: tuple[int, int], exp_prec: tuple[int, int] | None, exp_plus: bool | None, number_pattern: str | None=None) -> None:
        self.pattern = pattern
        self.prefix = prefix
        self.suffix = suffix
        self.number_pattern = number_pattern
        self.grouping = grouping
        self.int_prec = int_prec
        self.frac_prec = frac_prec
        self.exp_prec = exp_prec
        self.exp_plus = exp_plus
        self.scale = self.compute_scale()

    def __repr__(self) -> str:
        return f'<{type(self).__name__} {self.pattern!r}>'

    def compute_scale(self) -> Literal[0, 2, 3]:
        """Return the scaling factor to apply to the number before rendering.

        Auto-set to a factor of 2 or 3 if presence of a ``%`` or ``‰`` sign is
        detected in the prefix or suffix of the pattern. Default is to not mess
        with the scale at all and keep it to 0.
        """
        if '%' in ''.join(self.prefix + self.suffix):
            return 2
        elif '‰' in ''.join(self.prefix + self.suffix):
            return 3
        return 0

    def scientific_notation_elements(self, value: decimal.Decimal, locale: Locale | str | None, *, numbering_system: Literal['default'] | str='latn') -> tuple[decimal.Decimal, int, str]:
        """ Returns normalized scientific notation components of a value.
        """
        if isinstance(locale, str):
            locale = Locale.parse(locale)

        if numbering_system == 'default':
            numbering_system = locale.default_numbering_system

        try:
            exp_symbol = locale.number_symbols[numbering_system]['exponential']
        except KeyError:
            raise UnsupportedNumberingSystemError(f"Numbering system '{numbering_system}' is not supported for locale '{locale}'")

        exponent = 0
        if value != 0:
            while value >= 10 or value <= -10:
                exponent += 1
                value /= 10
            while value < 1 and value > -1:
                exponent -= 1
                value *= 10

        return value, exponent, exp_symbol

    def apply(self, value: float | decimal.Decimal | str, locale: Locale | str | None, currency: str | None=None, currency_digits: bool=True, decimal_quantization: bool=True, force_frac: tuple[int, int] | None=None, group_separator: bool=True, *, numbering_system: Literal['default'] | str='latn'):
        """Renders into a string a number following the defined pattern.

        Forced decimal quantization is active by default so we'll produce a
        number string that is strictly following CLDR pattern definitions.

        :param value: The value to format. If this is not a Decimal object,
                      it will be cast to one.
        :type value: decimal.Decimal|float|int
        :param locale: The locale to use for formatting.
        :type locale: str|babel.core.Locale
        :param currency: Which currency, if any, to format as.
        :type currency: str|None
        :param currency_digits: Whether or not to use the currency's precision.
                                If false, the pattern's precision is used.
        :type currency_digits: bool
        :param decimal_quantization: Whether decimal numbers should be forcibly
                                     quantized to produce a formatted output
                                     strictly matching the CLDR definition for
                                     the locale.
        :type decimal_quantization: bool
        :param force_frac: DEPRECATED - a forced override for `self.frac_prec`
                           for a single formatting invocation.
        :param numbering_system: The numbering system used for formatting number symbols. Defaults to "latn".
                                 The special value "default" will use the default numbering system of the locale.
        :return: Formatted decimal string.
        :rtype: str
        :raise UnsupportedNumberingSystemError: If the numbering system is not supported by the locale.
        """
        if isinstance(locale, str):
            locale = Locale.parse(locale)

        if isinstance(value, str):
            value = decimal.Decimal(value)
        elif not isinstance(value, decimal.Decimal):
            value = decimal.Decimal(str(value))

        is_negative = value < 0
        if self.scale:
            value = value * (10 ** self.scale)

        if currency and currency_digits:
            frac_prec = (get_currency_precision(currency), get_currency_precision(currency))
        elif force_frac:
            frac_prec = force_frac
        else:
            frac_prec = self.frac_prec

        if decimal_quantization:
            quantum = get_decimal_quantum(frac_prec[1])
            value = value.quantize(quantum)

        if numbering_system == 'default':
            numbering_system = locale.default_numbering_system

        try:
            symbols = locale.number_symbols[numbering_system]
        except KeyError:
            raise UnsupportedNumberingSystemError(f"Numbering system '{numbering_system}' is not supported for locale '{locale}'")

        value = abs(value)
        a, sep, b = f"{value:.{frac_prec[1]}f}".partition(".")

        if group_separator:
            a = self._format_int_part(a, self.grouping, symbols['group'])

        if b:
            b = b.rstrip('0')[:frac_prec[1]]
            if b:
                b = symbols['decimal'] + b

        number = a + b

        retval = ''
        if is_negative:
            retval += self.prefix[1]
        else:
            retval += self.prefix[0]

        retval += number

        if is_negative:
            retval += self.suffix[1]
        else:
            retval += self.suffix[0]

        return retval

    def _format_int_part(self, value: str, grouping: tuple[int, int], group_symbol: str) -> str:
        """Format the integer part of a number with grouping."""
        result = ''
        for i, digit in enumerate(reversed(value)):
            if i != 0 and i % grouping[0] == 0:
                result = group_symbol + result
            result = digit + result
        return result
