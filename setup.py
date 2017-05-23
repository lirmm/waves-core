import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='waves-core',
    version=__import__('waves').__version__,
    packages=find_packages(),
    provides=['waves'],
    include_package_data=True,
    license='GPLv3',
    description='WAVES - core ',
    url='http://waves.atgc-montpellier.fr',
    author='Marc Chakiachvili',
    author_email='marc.chakiachvili@lirmm.fr, marc@archi-logic.fr',
    install_requires=[
        'saga-python==0.45.1',
        'django-admin-sortable2==0.6.10',
        'django-crispy-forms==1.6.1',
        'django-mail-templated==2.6.5',
        'djangorestframework==3.5.4',
        'inflection==0.3.1',
        'pycrypto==2.6.1',
        'python-magic==0.4.13',
        'python-daemon==2.1.1',
        'psutil==5.2.2'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11.1',
        'Development Status :: 1 - Dev/Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPLv3 License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
        'Topic :: Web :: Distributed Computing',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: Unix'
    ],
)
