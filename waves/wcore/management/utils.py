import sys


def boolean_input(question, default=None):
    """
    Ask for a boolean response from user
    :param question: Question to ask
    :param default: Default answer
    :return: True or False
    :rtype: bool
    """
    result = raw_input("%s: " % question)
    if not result and default is not None:
        return default
    while len(result) < 1 or result[0].lower() not in "yn":
        result = raw_input("Please answer yes(y) or no(n): ")
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
    result = raw_input("Select an option: ")
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
    result = raw_input("%s (type Enter to keep default): " % question)
    if not result and default is not None:
        return default
    return str(result)


def action_cancelled(out):
    """
    Simply cancel current action, output confirmation
    """
    out.write('Action cancelled.')
    sys.exit(3)