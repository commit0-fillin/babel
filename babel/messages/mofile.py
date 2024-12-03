"""
    babel.messages.mofile
    ~~~~~~~~~~~~~~~~~~~~~

    Writing of files in the ``gettext`` MO (machine object) format.

    :copyright: (c) 2013-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import annotations
import array
import struct
from typing import TYPE_CHECKING
from babel.messages.catalog import Catalog, Message
if TYPE_CHECKING:
    from _typeshed import SupportsRead, SupportsWrite
LE_MAGIC: int = 2500072158
BE_MAGIC: int = 3725722773

def read_mo(fileobj: SupportsRead[bytes]) -> Catalog:
    """Read a binary MO file from the given file-like object and return a
    corresponding `Catalog` object.

    :param fileobj: the file-like object to read the MO file from

    :note: The implementation of this function is heavily based on the
           ``GNUTranslations._parse`` method of the ``gettext`` module in the
           standard library.
    """
    catalog = Catalog()
    buf = fileobj.read()
    buflen = len(buf)
    unpack = struct.unpack

    # Parse the magic number
    magic = unpack('<I', buf[:4])[0]
    if magic == LE_MAGIC:
        version, msgcount, masteridx, transidx = unpack('<4I', buf[4:20])
        ii = '<II'
    elif magic == BE_MAGIC:
        version, msgcount, masteridx, transidx = unpack('>4I', buf[4:20])
        ii = '>II'
    else:
        raise IOError('Invalid magic number')

    # Parse the version number
    if version not in (0, 1):
        raise IOError('Unknown MO file version')

    # Parse the catalog
    for i in range(msgcount):
        mlen, moff = unpack(ii, buf[masteridx:masteridx + 8])
        mend = moff + mlen
        tlen, toff = unpack(ii, buf[transidx:transidx + 8])
        tend = toff + tlen
        if mend > buflen or tend > buflen:
            raise IOError('File is corrupt')

        msg = buf[moff:mend]
        tmsg = buf[toff:tend]

        if b'\x00' in msg:
            # Plural forms
            msgid1, msgid2 = msg.split(b'\x00')
            tmsg = tmsg.split(b'\x00')
            if len(tmsg) > 1:
                catalog.add((msgid1.decode(), msgid2.decode()), [m.decode() for m in tmsg])
            else:
                catalog.add((msgid1.decode(), msgid2.decode()), tmsg[0].decode())
        else:
            catalog.add(msg.decode(), tmsg.decode())

        masteridx += 8
        transidx += 8

    return catalog

def write_mo(fileobj: SupportsWrite[bytes], catalog: Catalog, use_fuzzy: bool=False) -> None:
    """Write a catalog to the specified file-like object using the GNU MO file
    format.

    >>> import sys
    >>> from babel.messages import Catalog
    >>> from gettext import GNUTranslations
    >>> from io import BytesIO

    >>> catalog = Catalog(locale='en_US')
    >>> catalog.add('foo', 'Voh')
    <Message ...>
    >>> catalog.add((u'bar', u'baz'), (u'Bahr', u'Batz'))
    <Message ...>
    >>> catalog.add('fuz', 'Futz', flags=['fuzzy'])
    <Message ...>
    >>> catalog.add('Fizz', '')
    <Message ...>
    >>> catalog.add(('Fuzz', 'Fuzzes'), ('', ''))
    <Message ...>
    >>> buf = BytesIO()

    >>> write_mo(buf, catalog)
    >>> x = buf.seek(0)
    >>> translations = GNUTranslations(fp=buf)
    >>> if sys.version_info[0] >= 3:
    ...     translations.ugettext = translations.gettext
    ...     translations.ungettext = translations.ngettext
    >>> translations.ugettext('foo')
    u'Voh'
    >>> translations.ungettext('bar', 'baz', 1)
    u'Bahr'
    >>> translations.ungettext('bar', 'baz', 2)
    u'Batz'
    >>> translations.ugettext('fuz')
    u'fuz'
    >>> translations.ugettext('Fizz')
    u'Fizz'
    >>> translations.ugettext('Fuzz')
    u'Fuzz'
    >>> translations.ugettext('Fuzzes')
    u'Fuzzes'

    :param fileobj: the file-like object to write to
    :param catalog: the `Catalog` instance
    :param use_fuzzy: whether translations marked as "fuzzy" should be included
                      in the output
    """
    messages = list(catalog)
    messages.sort()

    ids = strs = b''
    offsets = []

    for message in messages:
        if not message.id or (not use_fuzzy and message.fuzzy) or not message.string:
            continue
        
        id = (message.context + '\x04' + message.id if message.context else message.id).encode('utf-8')
        string = message.string.encode('utf-8') if isinstance(message.string, str) else b'\x00'.join(s.encode('utf-8') for s in message.string)
        
        offsets.append((len(ids), len(id), len(strs), len(string)))
        ids += id + b'\x00'
        strs += string + b'\x00'

    # The header is 7 32-bit unsigned integers.
    keystart = 7 * 4 + 16 * len(offsets)
    valuestart = keystart + len(ids)
    koffsets = []
    voffsets = []
    for o in offsets:
        koffsets += [o[0] + keystart, o[1]]
        voffsets += [o[2] + valuestart, o[3]]
    offsets = koffsets + voffsets

    output = struct.pack('Iiiiiii',
        LE_MAGIC,                   # magic
        0,                          # version
        len(offsets) // 4,          # number of entries
        7 * 4,                      # start of key index
        7 * 4 + len(offsets) // 2,  # start of value index
        0, 0                        # size and offset of hash table
    ) + array.array("I", offsets).tobytes() + ids + strs

    fileobj.write(output)
