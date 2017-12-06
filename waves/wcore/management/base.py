from optparse import IndentedHelpFormatter

from django.core.management import BaseCommand


class SubcommandDispatcher(BaseCommand):
    """
    A template for a Django management command that dispatches to subcommands
    based on its first non-option argument

    For example, ``./manage.py crinkle hat 8`` would look up a new Command
    based on the "hat" string and invoke it with the "8" argument. Any options
    passed before the first non-option argument are considered meant for the
    dispatcher, while any after are passed along to the subcommand.

    Because ``SubcommandDispatcher`` re-invokes optparse for the subcommand,
    subcommands can have their own help: that is, ``./manage.py crinkle
    --help`` and ``./manage.py crinkle hat --help`` can return different
    things. It's a great way to hierarchalize an unwieldy number of management
    commands--or even generate them dynamically--while still getting all the
    Django management command framework stuff like settings access and
    integration with the ``./manage.py`` command.
    """
    subcommand = None

    # Override these:
    def add_arguments(self, parser):
        parser.add_argument('subcommand', choices=self._subcommand_names(), action='store', help="Accepted sub command")

    def _subcommand(self, name):
        """
        Return the management command instance to run.

        :arg name: The name of the subcommand. For example, if "unravel" were
            a subcommand, then ``./manage.py unravel hats 3`` would result in
            ``name`` being "hats".

        Override this to return a ``BaseCommand`` subclass instance. Return
        None if there is no such subcommand, and the dispatcher will print the
        help--including a summary of the valid subcommands if you implement
        ``_subcommand_names``.
        """
        raise NotImplementedError

    def _subcommand_names(self):
        """
        Return a list of the names of all the subcommands.

        Override this if you'd like ``./manage.py some_dispatcher --help`` to
        list all the subcommands and their arg summaries.
        """
        return []

    # Probably leave these alone:

    def create_parser(self, prog_name, subcommand):
        """
        Override ``BaseCommand``'s default implementation to add custom Formatter
        """
        parser = super(SubcommandDispatcher, self).create_parser(prog_name, subcommand)
        parser.allow_interspersed_args = False
        # Have it list the subcommands on --help:
        parser.formatter = SubcommandEpilogFormatter(subcommand_arg_summaries=self._subcommand_arg_summaries)
        parser.formatter.set_parser(parser)
        return parser

    def _subcommand_arg_summaries(self):
        """Return a description of all the subcommands and their arguments."""
        ret = []
        for name in self._subcommand_names():
            sub = self._subcommand(name)
            if sub:
                ret.append(' %s %s' % (name, sub.args))
            else:
                ret.append(' NOTE: The subcommand "%s" could not be retrieved'
                           ' from _subcommand(), even though '
                           '_subcommand_names() said it exists.' % name)
        return '\n'.join(ret)

    def run_from_argv(self, argv):
        """Dispatch to a subcommand."""
        # Parse argv just to count how many non-option args there are:
        self._called_from_command_line = True
        parser = self.create_parser(argv[0], argv[1])
        options = parser.parse_args(argv[2:3])
        cmd_options = vars(options)
        # Move positional args out of options to mimic legacy optparse
        args = cmd_options.pop('args', ())
        """
        if self.use_argparse:
            # only parse current
        else:
            options, args = parser.parse_args(argv[2:])
            cmd_options = vars(options)
        """
        # options, args = parser.parse_args(argv[2:])
        if 'subcommand' in cmd_options:  # You specified a subcommand.
            program, dispatcher, subcommand_name = argv[:3]
            subcommand = self._subcommand(subcommand_name)
            if subcommand:
                subcommand.run_from_argv([program + ' ' + dispatcher] + argv[2:])
                return
        self.print_help(argv[0], argv[1])

    def print_help(self, prog_name, subcommand):
        """
        Print the help message for this command, derived from
        ``self.usage()``.
        """
        parser = self.create_parser(prog_name, subcommand)
        parser.print_help()


class SubcommandEpilogFormatter(IndentedHelpFormatter):
    """Help formatter which lists the subcommands at the end"""

    def __init__(self, subcommand_arg_summaries, *args, **kwargs):
        self.subcommand_arg_summaries = subcommand_arg_summaries
        IndentedHelpFormatter.__init__(self, *args, **kwargs)

    def format_epilog(self, epilog):
        formatted_epilog = IndentedHelpFormatter.format_epilog(self, epilog)
        summaries = self.subcommand_arg_summaries()
        return ('%s\nSubcommands:\n%s\n' % (formatted_epilog, summaries) if
                summaries else formatted_epilog)
