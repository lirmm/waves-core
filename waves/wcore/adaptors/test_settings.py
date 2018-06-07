from __future__ import unicode_literals

# python 3 compatibility
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

from django.conf import settings
from os.path import join, isfile

configFile = join(settings.BASE_DIR, 'tests', 'settings.ini')
assert(isfile(configFile))
Config = ConfigParser.SafeConfigParser()
Config.read(configFile)

WAVES_TEST_SSH_HOST = Config.get('saga', 'WAVES_TEST_SSH_HOST')
WAVES_TEST_SSH_USER_ID = Config.get('saga', 'WAVES_TEST_SSH_USER_ID')
WAVES_TEST_SSH_USER_PASS = Config.get('saga', 'WAVES_TEST_SSH_USER_PASS')
WAVES_TEST_SSH_BASE_DIR = Config.get('saga', 'WAVES_TEST_SSH_BASE_DIR')

WAVES_LOCAL_TEST_SGE_CELL = Config.get('sge_cluster', 'WAVES_LOCAL_TEST_SGE_CELL')
WAVES_SSH_TEST_SGE_CELL = Config.get('sge_cluster', 'WAVES_SSH_TEST_SGE_CELL')
WAVES_SSH_TEST_SGE_BASE_DIR = Config.get('sge_cluster', 'WAVES_SSH_TEST_SGE_BASE_DIR')

WAVES_SSH_KEY_USER_ID = Config.get('ssh_key_cluster', 'WAVES_SSH_KEY_USER_ID')
WAVES_SSH_KEY_HOST = Config.get('ssh_key_cluster', 'WAVES_SSH_KEY_HOST')
WAVES_SSH_KEY_PASSPHRASE = Config.get('ssh_key_cluster', 'WAVES_SSH_KEY_PASSPHRASE')
WAVES_SSH_KEY_BASE_DIR = Config.get('ssh_key_cluster', 'WAVES_SSH_KEY_BASE_DIR')

WAVES_SLURM_TEST_SSH_HOST = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_HOST')
WAVES_SLURM_TEST_SSH_USER_ID = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_USER_ID')
WAVES_SLURM_TEST_SSH_USER_PASS = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_USER_PASS')
WAVES_SLURM_TEST_SSH_QUEUE = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_QUEUE')
WAVES_SLURM_TEST_SSH_BASE_DIR = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_BASE_DIR')
