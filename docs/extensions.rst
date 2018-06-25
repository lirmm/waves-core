================
WAVES Extensions
================


WAVES team provides some useful extensions or side project to WAVES-core:


Waves Demo
----------

    Side project to show examples for extending WAVES-core to fit your needs:

    - Extends Services , Submission
    - Override Service / submissions templates
    - Use of REST API forms
    - Use a different skin for the back-office interface
    - Custom front-end interface
    - Override the Authentication class

    See `demo github <https://github.com/lirmm/waves-demo>`_ repo for more details


Waves Galaxy
------------

    Galaxy dedicated adaptor, allows import and execution of services on remote Galaxy instances

    See `galaxy-adaptors github <https://github.com/lirmm/waves-galaxy>`_ repo for more details
    See `Documentation <http://waves-galaxy-adaptors.readthedocs.io/>`_



Just have a try
----------------

    This is a `Singularity <http://singularity.lbl.gov>`_ image containing a functional WAVES installation including two pre-configured services ('Hello world' and 'PhyML').
    It is a good way to test a fully operating WAVES-core instance.
    To be used with caution : all data will be lost when singularity instance is stopped.

    Singularity installation : on `Linux <http://singularity.lbl.gov/install-linux>`_ or `Mac <http://singularity.lbl.gov/install-mac>`_.

    Download WAVES test Singularity image : `wavetest.simg <http://www.atgc-montpellier.fr/download/binaries/waves/wavestest.simg>`_

    Example for Linux Debian ditribution ( Ubuntu 16.04 or later ) :

    Install Singularity :

    .. code-block:: bash

        sudo wget -O- http://neuro.debian.net/lists/xenial.us-ca.full | sudo tee /etc/apt/sources.list.d/neurodebian.sources.list
        sudo apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9
        sudo apt-get update
        sudo apt-get install -y singularity-container

    Get and use wavestest.simg (caution, you need to be sudoer to start an instance) :

    .. code-block:: bash
    
        wget http://www.atgc-montpellier.fr/download/binaries/waves/wavestest.simg
        sudo singularity instance.start wavestest.simg waves
        sudo singularity run instance://waves

    When the instance is launched, WAVES-core is running. Open localhost:8000 on your favorite browser. Login with "admin" and "motdepasse".

    Power off :
    
    .. code-block:: bash
        sudo singularity instance.stop waves

