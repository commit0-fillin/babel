from __future__ import annotations
import decimal
from typing import TYPE_CHECKING
from babel.core import Locale
from babel.numbers import LC_NUMERIC, format_decimal
if TYPE_CHECKING:
    from typing_extensions import Literal

class UnknownUnitError(ValueError):

    def __init__(self, unit: str, locale: Locale) -> None:
        ValueError.__init__(self, f'{unit} is not a known unit in {locale}')

def get_unit_name(measurement_unit: str, length: Literal['short', 'long', 'narrow']='long', locale: Locale | str | None=LC_NUMERIC) -> str | None:
    """
    Get the display name for a measurement unit in the given locale.

    >>> get_unit_name("radian", locale="en")
    'radians'

    Unknown units will raise exceptions:

    >>> get_unit_name("battery", locale="fi")
    Traceback (most recent call last):
        ...
    UnknownUnitError: battery/long is not a known unit/length in fi

    :param measurement_unit: the code of a measurement unit.
                             Known units can be found in the CLDR Unit Validity XML file:
                             https://unicode.org/repos/cldr/tags/latest/common/validity/unit.xml

    :param length: "short", "long" or "narrow"
    :param locale: the `Locale` object or locale identifier
    :return: The unit display name, or None.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    unit_data = locale.unit_display_names.get(measurement_unit)
    if unit_data is None:
        raise UnknownUnitError(f"{measurement_unit}/{length} is not a known unit/length in {locale}")

    return unit_data.get(length)

def _find_unit_pattern(unit_id: str, locale: Locale | str | None=LC_NUMERIC) -> str | None:
    """
    Expand a unit into a qualified form.

    Known units can be found in the CLDR Unit Validity XML file:
    https://unicode.org/repos/cldr/tags/latest/common/validity/unit.xml

    >>> _find_unit_pattern("radian", locale="en")
    'angle-radian'

    Unknown values will return None.

    >>> _find_unit_pattern("horse", locale="en")

    :param unit_id: the code of a measurement unit.
    :return: A key to the `unit_patterns` mapping, or None.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    for category in locale.unit_display_names:
        if unit_id in locale.unit_display_names[category]:
            return f"{category}-{unit_id}"
    return None

def format_unit(value: str | float | decimal.Decimal, measurement_unit: str, length: Literal['short', 'long', 'narrow']='long', format: str | None=None, locale: Locale | str | None=LC_NUMERIC, *, numbering_system: Literal['default'] | str='latn') -> str:
    """Format a value of a given unit.

    Values are formatted according to the locale's usual pluralization rules
    and number formats.

    >>> format_unit(12, 'length-meter', locale='ro_RO')
    u'12 metri'
    >>> format_unit(15.5, 'length-mile', locale='fi_FI')
    u'15,5 mailia'
    >>> format_unit(1200, 'pressure-millimeter-ofhg', locale='nb')
    u'1\\xa0200 millimeter kvikks\\xf8lv'
    >>> format_unit(270, 'ton', locale='en')
    u'270 tons'
    >>> format_unit(1234.5, 'kilogram', locale='ar_EG', numbering_system='default')
    u'1٬234٫5 كيلوغرام'

    Number formats may be overridden with the ``format`` parameter.

    >>> import decimal
    >>> format_unit(decimal.Decimal("-42.774"), 'temperature-celsius', 'short', format='#.0', locale='fr')
    u'-42,8\\u202f\\xb0C'

    The locale's usual pluralization rules are respected.

    >>> format_unit(1, 'length-meter', locale='ro_RO')
    u'1 metru'
    >>> format_unit(0, 'length-mile', locale='cy')
    u'0 mi'
    >>> format_unit(1, 'length-mile', locale='cy')
    u'1 filltir'
    >>> format_unit(3, 'length-mile', locale='cy')
    u'3 milltir'

    >>> format_unit(15, 'length-horse', locale='fi')
    Traceback (most recent call last):
        ...
    UnknownUnitError: length-horse is not a known unit in fi

    .. versionadded:: 2.2.0

    :param value: the value to format. If this is a string, no number formatting will be attempted.
    :param measurement_unit: the code of a measurement unit.
                             Known units can be found in the CLDR Unit Validity XML file:
                             https://unicode.org/repos/cldr/tags/latest/common/validity/unit.xml
    :param length: "short", "long" or "narrow"
    :param format: An optional format, as accepted by `format_decimal`.
    :param locale: the `Locale` object or locale identifier
    :param numbering_system: The numbering system used for formatting number symbols. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :raise `UnsupportedNumberingSystemError`: If the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    unit_pattern = _find_unit_pattern(measurement_unit, locale)
    if unit_pattern is None:
        raise UnknownUnitError(f"{measurement_unit} is not a known unit in {locale}")

    unit_name = get_unit_name(unit_pattern, length, locale)
    if unit_name is None:
        raise UnknownUnitError(f"{measurement_unit}/{length} is not a known unit/length in {locale}")

    if isinstance(value, str):
        formatted_value = value
    else:
        formatted_value = format_decimal(value, format=format, locale=locale, numbering_system=numbering_system)

    plural_form = locale.plural_form(value)
    unit_pattern = locale.unit_display_names[unit_pattern][length][plural_form]

    return unit_pattern.format(formatted_value, unit_name)

def _find_compound_unit(numerator_unit: str, denominator_unit: str, locale: Locale | str | None=LC_NUMERIC) -> str | None:
    """
    Find a predefined compound unit pattern.

    Used internally by format_compound_unit.

    >>> _find_compound_unit("kilometer", "hour", locale="en")
    'speed-kilometer-per-hour'

    >>> _find_compound_unit("mile", "gallon", locale="en")
    'consumption-mile-per-gallon'

    If no predefined compound pattern can be found, `None` is returned.

    >>> _find_compound_unit("gallon", "mile", locale="en")

    >>> _find_compound_unit("horse", "purple", locale="en")

    :param numerator_unit: The numerator unit's identifier
    :param denominator_unit: The denominator unit's identifier
    :param locale: the `Locale` object or locale identifier
    :return: A key to the `unit_patterns` mapping, or None.
    :rtype: str|None
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    for category, units in locale.unit_display_names.items():
        for unit, data in units.items():
            if '-per-' in unit:
                num, den = unit.split('-per-')
                if num == numerator_unit and den == denominator_unit:
                    return f"{category}-{unit}"
    return None

def format_compound_unit(numerator_value: str | float | decimal.Decimal, numerator_unit: str | None=None, denominator_value: str | float | decimal.Decimal=1, denominator_unit: str | None=None, length: Literal['short', 'long', 'narrow']='long', format: str | None=None, locale: Locale | str | None=LC_NUMERIC, *, numbering_system: Literal['default'] | str='latn') -> str | None:
    """
    Format a compound number value, i.e. "kilometers per hour" or similar.

    Both unit specifiers are optional to allow for formatting of arbitrary values still according
    to the locale's general "per" formatting specifier.

    >>> format_compound_unit(7, denominator_value=11, length="short", locale="pt")
    '7/11'

    >>> format_compound_unit(150, "kilometer", denominator_unit="hour", locale="sv")
    '150 kilometer per timme'

    >>> format_compound_unit(150, "kilowatt", denominator_unit="year", locale="fi")
    '150 kilowattia / vuosi'

    >>> format_compound_unit(32.5, "ton", 15, denominator_unit="hour", locale="en")
    '32.5 tons per 15 hours'

    >>> format_compound_unit(1234.5, "ton", 15, denominator_unit="hour", locale="ar_EG", numbering_system="arab")
    '1٬234٫5 طن لكل 15 ساعة'

    >>> format_compound_unit(160, denominator_unit="square-meter", locale="fr")
    '160 par m\\xe8tre carr\\xe9'

    >>> format_compound_unit(4, "meter", "ratakisko", length="short", locale="fi")
    '4 m/ratakisko'

    >>> format_compound_unit(35, "minute", denominator_unit="fathom", locale="sv")
    '35 minuter per famn'

    >>> from babel.numbers import format_currency
    >>> format_compound_unit(format_currency(35, "JPY", locale="de"), denominator_unit="liter", locale="de")
    '35\\xa0\\xa5 pro Liter'

    See https://www.unicode.org/reports/tr35/tr35-general.html#perUnitPatterns

    :param numerator_value: The numerator value. This may be a string,
                            in which case it is considered preformatted and the unit is ignored.
    :param numerator_unit: The numerator unit. See `format_unit`.
    :param denominator_value: The denominator value. This may be a string,
                              in which case it is considered preformatted and the unit is ignored.
    :param denominator_unit: The denominator unit. See `format_unit`.
    :param length: The formatting length. "short", "long" or "narrow"
    :param format: An optional format, as accepted by `format_decimal`.
    :param locale: the `Locale` object or locale identifier
    :param numbering_system: The numbering system used for formatting number symbols. Defaults to "latn".
                             The special value "default" will use the default numbering system of the locale.
    :return: A formatted compound value.
    :raise `UnsupportedNumberingSystemError`: If the numbering system is not supported by the locale.
    """
    if isinstance(locale, str):
        locale = Locale.parse(locale)

    if numerator_unit and denominator_unit:
        compound_unit = _find_compound_unit(numerator_unit, denominator_unit, locale)
        if compound_unit:
            return format_unit(numerator_value, compound_unit, length, format, locale, numbering_system=numbering_system)

    numerator = format_unit(numerator_value, numerator_unit, length, format, locale, numbering_system=numbering_system) if numerator_unit else str(numerator_value)
    denominator = format_unit(denominator_value, denominator_unit, length, format, locale, numbering_system=numbering_system) if denominator_unit else str(denominator_value)

    per_pattern = locale.unit_display_names.get('per', {}).get(length, '{0}/{1}')
    return per_pattern.format(numerator, denominator)
