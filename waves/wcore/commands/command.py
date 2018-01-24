from __future__ import unicode_literals

from waves.wcore.models.const import OptType


def command_line_element(cmd_format, name, cmd_value):
    if cmd_value == 'None':
        return ''
    if cmd_format == OptType.OPT_TYPE_VALUATED:
        return '--%s=%s' % (name, cmd_value)
    elif cmd_format == OptType.OPT_TYPE_SIMPLE:
        return '-%s %s' % (name, cmd_value)
    elif cmd_format == OptType.OPT_TYPE_OPTION:
        return '-%s' % name
    elif cmd_format == OptType.OPT_TYPE_NAMED_OPTION:
        return '--%s' % name
    elif cmd_format == OptType.OPT_TYPE_POSIX:
        return '%s' % cmd_value
    elif cmd_format == OptType.OPT_TYPE_NAMED_PARAM:
        return '%s=%s' % (name, cmd_value)
    elif cmd_format == OptType.OPT_TYPE_NONE:
        return ''
    # By default it's OPT_TYPE_SIMPLE way
    return '-%s %s' % (name, cmd_value)


class BaseCommand(object):

    def create_command_line(self, inputs):
        """
        Parse and create command line text to launch service
        Args:
            inputs: JobInput objects list

        Returns:
            str the command line text
        """
        return ' '.join(self.get_command_line_element_list(inputs))

    @staticmethod
    def get_command_line_element_list(inputs):
        if len(inputs) > 0:
            return [command_line_element(e.cmd_format, e.name, e.value) for e in inputs]
        else:
            return []
