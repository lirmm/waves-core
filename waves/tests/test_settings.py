from __future__ import unicode_literals

import ConfigParser
from os.path import join, dirname

configFile = join(dirname(__file__), 'settings.ini')
Config = ConfigParser.SafeConfigParser(
    dict(LOG_LEVEL='DEBUG',
         WAVES_TEST_SGE_CELL='mainqueue',
         WAVES_SSH_TEST_SGE_CELL='all.q')
)
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