""" WAVES specific ADMIN commands """

import json
import logging
import os
import uuid
from shutil import rmtree

# noinspection PyProtectedMember,PyProtectedMember
# from django.conf.urls import RegexURLPattern, RegexURLResolver
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from django.core.management import CommandError
from django.db import (
    DEFAULT_DB_ALIAS, transaction,
)
from rest_framework.exceptions import ValidationError

from waves.import_export.services import ServiceSerializer
from core.management.utils import choice_input
from waves.core.models import Job
from waves.core.settings import waves_settings as config

__all__ = ['CleanUpCommand', 'ImportCommand', 'DumpConfigCommand']

logger = logging.getLogger(__name__)


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
        for dir_name in os.listdir(config.JOB_BASE_DIR):
            try:
                # DO nothing, job exists in DB
                Job.objects.get(slug=uuid.UUID('{%s}' % dir_name))
            except ObjectDoesNotExist:
                removed.append(str(dir_name))
            except ValueError:
                pass
        if len(removed) > 0:
            while True:
                choice = choice_input(
                    "%i directory(ies) to be deleted, this operation is not reversible" % len(removed), choices=[
                        "List directories to delete",
                        "Perform delete",
                        "Exit"
                    ])
                if choice == 1:
                    self.stdout.write("Directories to delete: ")
                    for dir_name in removed:
                        self.stdout.write(os.path.join(config.JOB_BASE_DIR, dir_name))
                elif choice == 2:
                    for dir_name in removed:
                        self.stdout.write('Removed directory: %s' % dir_name)
                        # onerror(os.path.islink, path, sys.exc_info())
                        rmtree(os.path.join(config.JOB_BASE_DIR, dir_name),
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
        parser.add_argument('--skip_runner', action='store_true', dest="skip_run", default=False,
                            help="Skip import service runner")
        parser.add_argument('--database', action='store', dest='database',
                            default=DEFAULT_DB_ALIAS, help='Nominates a specific database to load '
                                                           'fixtures into. Defaults to the "default" database.')

    def handle(self, *args, **options):
        """ Handle import for services """
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
                    if db_version != config.DB_VERSION:
                        raise ValidationError('Uncompatible db versions')
                    if serializer.is_valid(raise_exception=True):
                        self.stdout.write("Service import from file %s ...." % exported_file)
                        serializer.validated_data['name'] += ' (Import)'
                        new_serv = serializer.save()
                        self.stdout.write(' > new service : %s' % new_serv)
                        self.stdout.write(
                            "... Done, you may edit service on: [your_waves_admin_host]%s " % new_serv.get_admin_url())
                except ValidationError as exc:
                    self.stderr.write('Data can not be import: %s' % exc.detail)
                except AssertionError as exc:
                    self.stderr.write('Data import error %s' % exc)

    def find_export_files(self, export, type_model):
        file_name = '%s_%s.json' % (type_model, export)
        export_file = os.path.join(config.DATA_ROOT, file_name)
        if os.path.isfile(export_file):
            return export_file
        else:
            raise CommandError("Unable to find exported file: %s, are they in your data root (%s)? " % (
                file_name, config.DATA_ROOT))


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
        from django.conf import settings
        self.stdout.write("************************************************")
        self.stdout.write('Current Django default database: %s' % settings.DATABASES['default']['ENGINE'])
        self.stdout.write('Current Django static dir: %s' % settings.STATICFILES_DIRS)
        self.stdout.write('Current Django static root: %s' % settings.STATIC_ROOT)
        self.stdout.write('Current Django media path: %s' % settings.MEDIA_ROOT)
        self.stdout.write('Current Django allowed hosts: %s' % settings.ALLOWED_HOSTS)
        self.stdout.write("************************************************")
        self.stdout.write("****  WAVES current setup *****")
        for key, val in settings.WAVES_CORE.items():
            self.stdout.write('%s: %s' % (key, val))
        self.stdout.write("************************************************")
