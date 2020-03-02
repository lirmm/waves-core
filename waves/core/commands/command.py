"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
from waves.core.const import OptType


def command_line_element(elem):
    cmd_format = elem.cmd_format
    name = elem.name
    cmd_value = elem.value if elem.required is not None else elem.default
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
            return [command_line_element(e) for e in inputs]
        else:
            return []
