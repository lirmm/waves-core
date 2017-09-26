from __future__ import unicode_literals

__all__ = [
    'OPT_TYPE_NONE',
    'OPT_TYPE_VALUATED',
    'OPT_TYPE_SIMPLE',
    'OPT_TYPE_OPTION',
    'OPT_TYPE_POSIX',
    'OPT_TYPE_NAMED_OPTION',
    'OPT_TYPE_NAMED_PARAM',
    'OPT_TYPE',
    'TYPE_BOOLEAN',
    'TYPE_FILE',
    'TYPE_LIST',
    'TYPE_DECIMAL',
    'TYPE_TEXT',
    'TYPE_INT',
    'IN_TYPE',
]


OPT_TYPE_NONE = 0
OPT_TYPE_VALUATED = 1
OPT_TYPE_SIMPLE = 2
OPT_TYPE_OPTION = 3
OPT_TYPE_POSIX = 4
OPT_TYPE_NAMED_OPTION = 5
OPT_TYPE_NAMED_PARAM = 6
OPT_TYPE = [
    (OPT_TYPE_NONE, "Not used in final command"),
    (OPT_TYPE_NAMED_PARAM, '[name]=value'),
    (OPT_TYPE_SIMPLE, '-[name] value'),
    (OPT_TYPE_VALUATED, '--[name]=value'),
    (OPT_TYPE_OPTION, '-[name]'),
    (OPT_TYPE_NAMED_OPTION, '--[name]'),
    (OPT_TYPE_POSIX, 'value')
]
TYPE_BOOLEAN = 'boolean'
TYPE_FILE = 'file'
TYPE_LIST = 'list'
TYPE_DECIMAL = 'decimal'
TYPE_TEXT = 'text'
TYPE_INT = 'int'
IN_TYPE = [
    (TYPE_FILE, 'Input file'),
    (TYPE_LIST, 'List of values'),
    (TYPE_BOOLEAN, 'Boolean'),
    (TYPE_DECIMAL, 'Decimal'),
    (TYPE_INT, 'Integer'),
    (TYPE_TEXT, 'Text')
]
