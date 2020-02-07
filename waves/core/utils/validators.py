from __future__ import unicode_literals

import os
import logging

from django.core.exceptions import ValidationError

from waves.core.models.const import ParamType
logger = logging.getLogger(__name__)

# TODO activate dedicated validators for job Input [https://docs.djangoproject.com/en/1.9/ref/validators/]
class ServiceInputValidator(object):
    """
    Dynamic validation class for SubmissionParam objects, according to SubmissionParam param_type and format
    """
    invalid_message = '%s is not valid %s (%s) got: %s'
    specific_message = ''

    def validate_input(self, the_input, value, form):
        try:
            validator = '_validate_input_' + the_input.type
            func = getattr(self, validator)
            if type(value) == list:
                valid = True
                for val in value:
                    valid = valid and func(the_input, val)
            else:
                valid = func(the_input, value)
            if not valid:
                form.add_error(the_input.name,
                               self.invalid_message % (the_input.label, the_input.type, self.specific_message, value))
            return True
        except AssertionError as e:
            form.add_error(the_input.name, 'Wrong input "%s": %s' % (the_input, e.message))
        except AttributeError as e:
            logger.exception("AdaptorException in %s: %s", adaptor.__class__.__name__, e.message)
            form.add_error(the_input.name,
                           'Unknown param_type for input: %s - param_type: %s' % (the_input, the_input.type))

    def _validate_input_boolean(self, the_input, value):
        # Add check format values
        self.specific_message = ' allowed values are "yes", "true", "1", "no", "false", "0", "None"'
        return str(value).lower() in ("yes", "true", "1", 'no', 'false', '0', 'none') and type(
            value) == bool and the_input.type == ParamType.TYPE_BOOLEAN

    def _validate_input_file(self, the_input, value):
        from django.core.files.base import File
        assert the_input.type == ParamType.TYPE_FILE
        self.specific_message = 'allowed extension are %s' % str([e[1] for e in the_input.choices])
        # TODO Check file consistency with BioPython ?
        filter_extension = the_input.choices
        if filter_extension:
            if type(value) == list:
                assert all(isinstance(_, File) for _ in value), '%s is not a valid File' % value
                result = True
                for up_file in value:
                    _, extension = os.path.splitext(up_file.name)
                    result = result and (any(e[1] == extension for e in filter_extension))
                    return result
            else:
                assert isinstance(value, File), '%s is not a valid File' % value
                _, extension = os.path.splitext(value.name)
                return any(e[1] == extension for e in filter_extension)
        return True

    def _validate_input_int(self, the_input, value):
        assert the_input.type == ParamType.TYPE_INT
        self.specific_message = 'value %s is not a valid integer' % value
        if not the_input.mandatory and value is None:
            return True
        try:
            int(value)
            if the_input.format:
                # TODO check min max
                pass
            return True
        except TypeError:
            return False

    def _validate_input_number(self, the_input, value):
        return self._validate_input_int(the_input, value)

    def _validate_input_float(self, the_input, value):
        assert the_input.type == ParamType.TYPE_DECIMAL
        self.specific_message = 'value %s is not a valid float' % value
        if not the_input.mandatory and value is None:
            return True
        try:
            float(value)
            if the_input.format:
                # TODO check min max
                pass
            return True
        except TypeError:
            return False

    def _validate_input_select(self, the_input, value):
        self.specific_message = 'allowed values are %s' % str([e[1] for e in the_input.choices])
        return any(e[0] == value for e in the_input.choices)

    def _validate_input_text(self, the_input, value):
        assert the_input.type == ParamType.TYPE_TEXT
        assert isinstance(value, str) or value is None, 'value %s is not a valid string' % value
        self.specific_message = 'value %s is not a valid string' % value
        return True


def validate_list_comma(value):
    import re
    if not re.match("(\w,)*", value):
        raise ValidationError('Wrong format for list: comma separated only')


def validate_list_param(value):
    import re
    pattern = re.compile(r"^.+\|[\w+;\-,:\"?']+$", re.MULTILINE)
    if not all([pattern.match(val) for val in value.splitlines()]):
        raise ValidationError('Wrong format for list elements : spaces allowed for labels, not for values')


def validate_name_param(value):
    import re
    pattern = re.compile('^[A-Za-z]+[A-Za-z0-9]*$')
    if not pattern.match(value):
        raise ValidationError('Wrong parameter name : one word, no space, char followed by char or number')
