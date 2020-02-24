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
from django.utils.module_loading import import_string, import_module


def get_commands_impl_list():
    classes_list = [('', 'Select a implementation class...')]
    mod = import_module('waves.core.commands')
    for cls in sorted(mod.__all__):
        clazz = import_string(mod.__name__ + '.' + cls)
        classes_list.append((clazz.__module__ + '.' + clazz.__name__, clazz.__name__))
    return classes_list
