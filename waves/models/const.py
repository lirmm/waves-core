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

__all__ = ['OptType', 'ParamType']


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