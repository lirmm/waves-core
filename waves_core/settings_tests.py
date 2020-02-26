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
from .settings import *

import configparser

WAVES_BASE_DIR = os.path.join(BASE_DIR, 'tests')

# WAVES
ADAPTORS_DEFAULT_CLASSES = (
    'waves.tests.mocks.MockJobRunnerAdaptor',
)

WAVES_CORE = {
    'ACCOUNT_ACTIVATION_DAYS': 14,
    'ADMIN_EMAIL': 'admin@waves.atgc-montpellier.fr',
    'DATA_ROOT': os.path.join(WAVES_BASE_DIR, 'data'),
    'JOB_LOG_LEVEL': 'DEBUG',
    'JOB_BASE_DIR': os.path.join(WAVES_BASE_DIR, 'data', 'jobs'),
    'BINARIES_DIR': os.path.join(WAVES_BASE_DIR, 'data', 'bin'),
    'SAMPLE_DIR': os.path.join(WAVES_BASE_DIR, 'data', 'sample'),
    'KEEP_ANONYMOUS_JOBS': 2,
    'KEEP_REGISTERED_JOBS': 30,
    'ALLOW_JOB_SUBMISSION': True,
    'APP_NAME': 'WAVES CORE',
    'SERVICES_EMAIL': 'contact@waves.atgc-montpellier.fr',
    'ADAPTORS_CLASSES': ADAPTORS_DEFAULT_CLASSES,
}

# CONF EMAIL
URL_BROKER = "redis://localhost:6379"
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
APP_LOG_LEVEL = 'DEBUG'

TEST_DATA_ROOT = os.path.join(BASE_DIR, "tests", 'data')
LOG_DIR = os.path.join(TEST_DATA_ROOT, 'logs')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s][%(asctime)s][%(name)s.%(funcName)s:%(lineno)s] - %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'ERROR',
        },
        'waves': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'rest_framework.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

configFile = os.path.join(BASE_DIR, 'waves', 'core', 'tests', 'settings.ini')

try:
    assert (os.path.isfile(configFile))
    Config = configparser.RawConfigParser()
    Config.read(configFile)
    try:
        WAVES_TEST_SSH_HOST = Config.get('ssh', 'WAVES_TEST_SSH_HOST', fallback='localhost')
        WAVES_TEST_SSH_USER_ID = Config.get('ssh', 'WAVES_TEST_SSH_USER_ID', fallback='root')
        WAVES_TEST_SSH_USER_PASS = Config.get('ssh', 'WAVES_TEST_SSH_USER_PASS', fallback='root')
        WAVES_TEST_SSH_BASE_DIR = Config.get('ssh', 'WAVES_TEST_SSH_BASE_DIR', fallback='localhost')
        WAVES_TEST_SSH_PORT = Config.get('ssh', 'WAVES_TEST_SSH_PORT', fallback=2222)
    except configparser.NoSectionError:
        # don't load if no entry
        WAVES_TEST_SSH_HOST = 'localhost'
        WAVES_TEST_SSH_USER_ID = '%USER%'
        WAVES_TEST_SSH_USER_PASS = 'passwaves'
        WAVES_TEST_SSH_BASE_DIR = '%HOMEDIR%'
        WAVES_TEST_SSH_PORT = '2222'
    try:
        WAVES_LOCAL_TEST_SGE_CELL = Config.get('sge', 'WAVES_LOCAL_TEST_SGE_CELL')
        WAVES_SSH_TEST_SGE_HOST = Config.get('sge', 'WAVES_LOCAL_TEST_SGE_CELL')
        WAVES_SSH_TEST_SGE_CELL = Config.get('sge', 'WAVES_SSH_TEST_SGE_CELL')
        WAVES_SSH_TEST_SGE_BASE_DIR = Config.get('sge', 'WAVES_SSH_TEST_SGE_BASE_DIR')
    except configparser.NoSectionError:
        WAVES_LOCAL_TEST_SGE_CELL = 'all'
        WAVES_SSH_TEST_SGE_HOST = 'localhost'
        WAVES_SSH_TEST_SGE_CELL = 'all'
        WAVES_SSH_TEST_SGE_BASE_DIR = '%HOMEDIR%'
    try:
        WAVES_SLURM_TEST_SSH_HOST = Config.get('slurm', 'WAVES_SLURM_TEST_SSH_HOST')
        WAVES_SLURM_TEST_SSH_USER_ID = Config.get('slurm', 'WAVES_SLURM_TEST_SSH_USER_ID')
        WAVES_SLURM_TEST_SSH_USER_PASS = Config.get('slurm', 'WAVES_SLURM_TEST_SSH_USER_PASS')
        WAVES_SLURM_TEST_SSH_QUEUE = Config.get('slurm', 'WAVES_SLURM_TEST_SSH_QUEUE')
        WAVES_SLURM_TEST_SSH_BASE_DIR = Config.get('slurm', 'WAVES_SLURM_TEST_SSH_BASE_DIR')
    except configparser.NoSectionError:
        WAVES_SLURM_TEST_SSH_HOST = 'localhost'
        WAVES_SLURM_TEST_SSH_USER_ID = '%USER%'
        WAVES_SLURM_TEST_SSH_USER_PASS = 'passwaves'
        WAVES_SLURM_TEST_SSH_QUEUE = 'queue'
        WAVES_SLURM_TEST_SSH_BASE_DIR = '%HOMEDIR%'

except AssertionError:
    # Don't load variables from ini files they are initialized elsewhere (i.e lab ci)
    pass
