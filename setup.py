import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()


def import_version():
    from waves.wcore import __version_detail__
    return __version_detail__


def import_requirements():
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
        content = f.readlines()
        # you may also want to remove whitespace characters like `\n` at the end of each line
        content = [x.strip() for x in content]
        return content

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='waves-core',
    version=import_version(),
    packages=find_packages(),
    provides=['waves'],
    include_package_data=True,
    license='GPLv3',
    description='WAVES - core package',
    url='http://waves.atgc-montpellier.fr',
    author='Marc Chakiachvili',
    author_email='marc.chakiachvili@gmail.com',
    install_requires=import_requirements(),
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
