""" WAVES specific ADMIN commands """
from __future__ import unicode_literals

import json
import logging
import os
import sys
import uuid
from shutil import rmtree

from constance import config
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand, CommandError
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.db import (
    DEFAULT_DB_ALIAS, transaction,
)
from rest_framework.exceptions import ValidationError

import waves.exceptions
import waves.settings
from waves.compat import available_themes
from waves.models import Job
from waves.models.serializers.services import ServiceSerializer

__all__ = ['InitDbCommand', 'CleanUpCommand', 'ImportCommand',
           'DumpConfigCommand', 'CreateDefaultRunner']

logger = logging.getLogger(__name__)


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


class InitDbCommand(BaseCommand):
    """ Initialise WAVES DB with default values """
    help = "Init DB data - :WARNING: reset data to its origin"

    def handle(self, *args, **options):
        """ Handle InitDB command """
        from waves.models import Service, ServiceCategory
        self.stdout.write(self.style.WARNING('Warning, this action reset ALL waves data to initial'))
        process = False
        if boolean_input("Do you want to proceed ? [y/N]", False):
            process = True
        if process:
            # Delete all WAVES data
            ServiceCategory.objects.all().delete()
            Service.objects.all().delete()
            Job.objects.all().delete()
            try:
                self.stdout.write("Configuring WAVES application:")
                site_theme = choice_input('Choose your bootstrap theme (def:%s)' % config.WAVES_BOOTSTRAP_THEME,
                                          choices=[theme[1] for theme in available_themes],
                                          default=6)
                call_command('constance', 'set', 'WAVES_BOOTSTRAP_THEME', available_themes[site_theme-1][0])
                self.stdout.write("... Done")
                allow_registration = boolean_input("Do you want to allow user registration ? [y/N]", False)
                call_command('constance', 'set', 'WAVES_REGISTRATION_ALLOWED', bool(allow_registration))
                self.stdout.write("... Done")
                allow_submits = boolean_input("Do you want to allow job submissions ? [y/N]", False)
                call_command('constance', 'set', 'WAVES_ALLOW_JOB_SUBMISSION', bool(allow_submits))
                self.stdout.write("... Done")
                call_command('constance', 'set', 'WAVES_SITE_MAINTENANCE', True)
                self.stdout.write("Your site configuration is ready, site is currently in 'maintenance' mode")
                # TODO add ask for import sample services ?
                if boolean_input("Do you want to create a superadmin user ? [y/N]", False):
                    call_command('createsuperuser')
                self.stdout.write('Your WAVES data are ready :-)')
            except Exception as exc:
                self.stderr.write('Error occurred, you database may be inconsistent ! \n %s - %s ' % (
                    exc.__class__.__name__, str(exc)))
        else:
            action_cancelled(self.stdout)


class CreateDefaultRunner(BaseCommand):
    """
    WAVES command to init default runner issued from available classes in PYTHON path
    """
    def handle(self, *args, **options):
        from waves.models import Runner
        if boolean_input('Do you wish to erase current runners ? [y/N]', False):
            Runner.objects.all().delete()
        try:
            self.stdout.write('Creating runners ...')
            from waves.utils.runners import get_runners_list
            for clazz in get_runners_list(flat=True):
                Runner.objects.create(name="%s Runner" % clazz[1], clazz=clazz[0])
                self.stdout.write("Created 'Runner Adaptor: %s'" % clazz[1])
            self.stdout.write("... Ready !")
        except Exception as exc:
            self.stderr.write('Error occurred, you database may be inconsistent ! \n %s - %s ' % (
                exc.__class__.__name__, str(exc)))


class CleanUpCommand(BaseCommand):
    """ Clean up file system according to jobs in database """
    help = "Clean up inconsistent data on disk related to jobs"

    # args = '[--from-date date] to limit clean up until date'
    def print_file_error(self, islink, path, exe_info):
        self.stderr.write("Unable to remove dir %s (%s)" % (path, exe_info))

    def add_arguments(self, parser):
        parser.add_argument('--to-date', default=None, help="Restrict purge to a date (anterior)")

    def handle(self, *args, **options):
        removed = []
        for dir_name in os.listdir(waves.settings.WAVES_JOB_DIR):
            try:
                # DO nothing, job exists in DB
                Job.objects.get(slug=uuid.UUID('{%s}' % dir_name))
            except ObjectDoesNotExist:
                removed.append(str(dir_name))
            except ValueError:
                pass
        if len(removed) > 0:
            while True:
                choice = choice_input("%i directory(ies) to be deleted, this operation is not reversible" % len(removed), choices=[
                        "List directories to delete",
                        "Perform delete",
                        "Exit"
                    ])
                if choice == 1:
                    self.stdout.write("Directories to delete: ")
                    for dir_name in removed:
                        self.stdout.write(os.path.join(waves.settings.WAVES_JOB_DIR, dir_name))
                elif choice == 2:
                    for dir_name in removed:
                        self.stdout.write('Removed directory: %s' % dir_name)
                        # onerror(os.path.islink, path, sys.exc_info())
                        rmtree(os.path.join(waves.settings.WAVES_JOB_DIR, dir_name),
                               onerror=self.print_file_error)
                    removed = []
                else:
                    break
            self.stdout.write("...Bye")
        else:
            self.stdout.write("Your jobs data dir is sane, nothing wrong here")


class ImportCommand(BaseCommand):
    """ Load and create a new service from a previously exported service from WAVES backoffice """
    help = "Load a previously exported service into your WAVES instance"

    def add_arguments(self, parser):
        parser.add_argument('type_model', type=str, action="store",
                            choices=('service', 'runner'),
                            help="Type of data to import (service, runner)")
        parser.add_argument('args', metavar='export_id', nargs='+', help='Previously exported data.')
        parser.add_argument('--skip_category', action='store_true', dest="skip_cat", default=False,
                            help="Skip import service category")
        parser.add_argument('--skip_runner', action='store_true', dest="skip_run", default=False,
                            help="Skip import service runner")
        parser.add_argument('--database', action='store', dest='database',
                            default=DEFAULT_DB_ALIAS, help='Nominates a specific database to load '
                                                           'fixtures into. Defaults to the "default" database.')

    def handle(self, *args, **options):
        """ Handle import for services """
        # TODO handle single Runner / import export
        exported_files = []
        type_mode = options.get('type_model', 'service')
        if type_mode != 'service':
            raise CommandError('Sorry, only services can be imported for the moment')
        for export in args:
            exported_files.append(self.find_export_files(export, type_mode))
        using = options.get('database')
        for exported_file in exported_files:
            with transaction.atomic(using=using) and open(exported_file) as fp:
                json_srv = json.load(fp)
                if type_mode == 'service':
                    serializer = ServiceSerializer(data=json_srv, skip_cat=options.get('skip_cat'),
                                                   skip_run=options.get('skip_run'))
                else:
                    raise NotImplementedError('Currently only services can be imported')
                try:
                    db_version = json_srv.pop('db_version', None)
                    if serializer.is_valid(raise_exception=True):
                        self.stdout.write("Service import from file %s ...." % exported_file)
                        serializer.validated_data['name'] += ' (Import)'
                        new_serv = serializer.save()
                        self.stdout.write(' > new service : %s' % new_serv)
                        self.stdout.write(
                            "... Done, you may edit service on: [your_waves_admin_host]%s " % reverse(
                                'admin:waves_service_change',
                                args=[new_serv.id]))
                except ValidationError as exc:
                    self.stderr.write('Data can not be import: %s' % exc.detail)
                except AssertionError as exc:
                    self.stderr.write('Data import error %s' % exc)

    def find_export_files(self, export, type_model):
        file_name = '%s_%s.json' % (type_model, export)
        export_file = os.path.join(config.WAVES_DATA_ROOT, file_name)
        if os.path.isfile(export_file):
            return export_file
        else:
            raise CommandError("Unable to find exported file: %s, are they in your data root (%s)? " % (
                file_name, config.WAVES_DATA_ROOT))


class DumpConfigCommand(BaseCommand):
    """
    Dedicated command to summarize current WAVES specific settings
    """
    help = 'Dump all WAVES configuration setup'

    def handle(self, *args, **options):
        """
        Handle command in Django command line interface
        Print out to standard output current WAVES configuration.

        :param args: Command arguments (expected none)
        :param options: Command options (expected none)
        """
        import waves.settings
        from django.conf import settings
        var_dict = vars(waves.settings)
        self.stdout.write("*******************************")
        self.stdout.write("****  WAVES current setup *****")
        self.stdout.write("*******************************")
        self.stdout.write('Current Django default database: %s' % settings.DATABASES['default']['ENGINE'])
        self.stdout.write('Current Django static dir: %s' % settings.STATICFILES_DIRS)
        self.stdout.write('Current Django static root: %s' % settings.STATIC_ROOT)
        self.stdout.write('Current Django media path: %s' % settings.MEDIA_ROOT)
        self.stdout.write('Current Django allowed hosts: %s' % settings.ALLOWED_HOSTS)
        self.stdout.write("********* CONFIGURED IN local.env **************")
        for key in sorted(var_dict.keys()):
            if key.startswith('WAVES'):
                self.stdout.write('%s: %s' % (key, var_dict[key]))
        self.stdout.write("************************************************")
