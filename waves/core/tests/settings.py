from waves_core.settings import *
import configparser
WAVES_BASE_DIR = os.path.join(BASE_DIR, 'tests')
# WAVES
ADAPTORS_DEFAULT_CLASSES = (
    'waves.core.adaptors.saga.shell.SshShellAdaptor',
    'waves.core.adaptors.saga.cluster.LocalClusterAdaptor',
    'waves.core.adaptors.saga.shell.SshKeyShellAdaptor',
    'waves.core.adaptors.saga.shell.LocalShellAdaptor',
    'waves.core.adaptors.saga.cluster.SshClusterAdaptor',
    'waves.core.adaptors.saga.cluster.SshKeyClusterAdaptor',
    # 'waves.core.tests.mocks.MockJobRunnerAdaptor'
)

WAVES_CORE = {
    'ACCOUNT_ACTIVATION_DAYS': 14,
    'ADMIN_EMAIL': 'admin@waves.atgc-montpellier.fr',
    'DATA_ROOT': os.path.join(BASE_DIR, 'data'),
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
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages'  # change this to a proper location

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
        WAVES_TEST_SSH_HOST = Config.get('ssh', 'WAVES_TEST_SSH_HOST')
        WAVES_TEST_SSH_USER_ID = Config.get('ssh', 'WAVES_TEST_SSH_USER_ID')
        WAVES_TEST_SSH_USER_PASS = Config.get('ssh', 'WAVES_TEST_SSH_USER_PASS')
        WAVES_TEST_SSH_BASE_DIR = Config.get('ssh', 'WAVES_TEST_SSH_BASE_DIR')
        WAVES_TEST_SSH_PORT = Config.get('ssh', 'WAVES_TEST_SSH_PORT')
    except configparser.NoSectionError:
        # don't load if no entry
        pass
    try:
        WAVES_LOCAL_TEST_SGE_CELL = Config.get('sge_cluster', 'WAVES_LOCAL_TEST_SGE_CELL')
        WAVES_SSH_TEST_SGE_CELL = Config.get('sge_cluster', 'WAVES_SSH_TEST_SGE_CELL')
        WAVES_SSH_TEST_SGE_BASE_DIR = Config.get('sge_cluster', 'WAVES_SSH_TEST_SGE_BASE_DIR')
    except configparser.NoSectionError:
        # don't load if no entry
        pass
    try:
        WAVES_SSH_KEY_USER_ID = Config.get('ssh_key_cluster', 'WAVES_SSH_KEY_USER_ID')
        WAVES_SSH_KEY_HOST = Config.get('ssh_key_cluster', 'WAVES_SSH_KEY_HOST')
        WAVES_SSH_KEY_PASSPHRASE = Config.get('ssh_key_cluster', 'WAVES_SSH_KEY_PASSPHRASE')
        WAVES_SSH_KEY_BASE_DIR = Config.get('ssh_key_cluster', 'WAVES_SSH_KEY_BASE_DIR')
    except configparser.NoSectionError:
        # don't load if no entry
        pass
    try:
        WAVES_SLURM_TEST_SSH_HOST = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_HOST')
        WAVES_SLURM_TEST_SSH_USER_ID = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_USER_ID')
        WAVES_SLURM_TEST_SSH_USER_PASS = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_USER_PASS')
        WAVES_SLURM_TEST_SSH_QUEUE = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_QUEUE')
        WAVES_SLURM_TEST_SSH_BASE_DIR = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_BASE_DIR')
    except configparser.NoSectionError:
        # don't load if no entry
        pass

except AssertionError:
    # Don't load variables from ini files they are initialized elsewhere (i.e lab ci)
    pass

# Broker configuration for celery
URL_BROKER = "redis://localhost:6379"
# CONF EMAIL TODO CHANGE BACKEND TO CONSOLE FOR TESTS
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

