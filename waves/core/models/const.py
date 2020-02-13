__all__ = []


class OptType(object):
    OPT_TYPE_NONE = 0
    OPT_TYPE_VALUATED = 1
    OPT_TYPE_SIMPLE = 2
    OPT_TYPE_OPTION = 3
    OPT_TYPE_POSIX = 4
    OPT_TYPE_NAMED_OPTION = 5
    OPT_TYPE_NAMED_PARAM = 6
    OPT_TYPE = [
        (OPT_TYPE_NONE, "-- Not used in job command line--"),
        (OPT_TYPE_NAMED_PARAM, 'Assigned named parameter: [name]=value'),
        (OPT_TYPE_SIMPLE, 'Named short parameter: -[name] value'),
        (OPT_TYPE_VALUATED, 'Named assigned long parameter: --[name]=value'),
        (OPT_TYPE_OPTION, 'Named short option: -[name]'),
        (OPT_TYPE_NAMED_OPTION, 'Named long option: --[name]'),
        (OPT_TYPE_POSIX, 'Positional parameter: value')
    ]


class ParamType(object):
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