from __future__ import unicode_literals

import re
import unicodedata
from waves.wcore.adaptors.exceptions import AdaptorNotReady


def check_ready(func):
    def inner(self, *args, **kwargs):
        if not all([value is not None for init_param, value in self.init_params.items()]):
            # search missing values
            raise AdaptorNotReady(
                "Missing required parameter(s) for initialization: %s " % [init_param for init_param, value in
                                                                           self.init_params.items() if value is None])
        else:
            return func(self, *args, **kwargs)
    return inner


def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
        value = re.sub('[^\w\s-]', '', value, flags=re.U).strip().lower()
        return re.sub('[-\s]+', '-', value, flags=re.U)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    import importlib
    try:
        print "dotted path ", dotted_path
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        raise ImportError(msg)

    module = importlib.import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
        raise ImportError(msg)
