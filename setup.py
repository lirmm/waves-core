import os
from setuptools import find_packages, setup


def import_version():
    from waves.wcore import __version__
    return __version__


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='waves-core',
    version=import_version(),
    packages=find_packages(),
    provides=['waves', 'waves'],
    include_package_data=True,
    license='GPLv3',
    description='WAVES - core ',
    url='http://waves.atgc-montpellier.fr',
    author='Marc Chakiachvili',
    author_email='marc.chakiachvili@lirmm.fr, marc@archi-logic.fr',
    install_requires=[
        'saga-python==0.46',
        'Django==1.11.5',
        'django-crispy-forms==1.6.1',
        'djangorestframework==3.5.4',
        'django-polymorphic==1.2',
        'inflection==0.3.1',
        'pycrypto==2.6.1',
        'python-magic==0.4.13',
        'psutil==5.2.2',
        'swapper==1.1.0',
        'setproctitle==1.1.10',
        'django-admin-sortable2==0.6.16',
        'daemons==1.3.0',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
        'Topic :: System :: Distributed Computing',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Operating System :: Unix'
    ],
)
