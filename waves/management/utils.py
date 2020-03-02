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

import sys


def boolean_input(question, default=None):
    """
    Ask for a boolean response from user
    :param question: Question to ask
    :param default: Default answer
    :return: True or False
    :rtype: bool
    """
    result = input("%s: " % question)
    if not result and default is not None:
        return default
    while len(result) < 1 or result[0].lower() not in "yn":
        result = input("Please answer yes(y) or no(n): ")
    return result[0].lower() == "y"


def choice_input(question, choices, default=None):
    """
    Ask user for choice in a list, indexed by integer response

    :param default:
    :param question: The question to ask
    :param choices: List of possible choices
    :return: Selected choice by user
    :rtype: int
    """
    print("%s:" % question)
    for i, choice in enumerate(choices):
        print("-%s) %s" % (i + 1, choice))
    result = input("Select an option: ")
    try:
        value = int(result)
        if 0 < value <= len(choices):
            return value
    except ValueError:
        if default:
            return default
        else:
            return choice_input('Please select a valid value', choices, default)


def text_input(question, default=None):
    result = input("%s (type Enter to keep default): " % question)
    if not result and default is not None:
        return default
    return str(result)


def action_cancelled(out):
    """
    Simply cancel current action, output confirmation
    """
    out.write('Action cancelled.')
    sys.exit(3)
