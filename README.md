README
======

What is WAVES for ?
-------------------

WAVES stands for "\ **W**\ eb \ **A**\ pplication for \ **V**\ ersatile and \ **E**\ asy online bioinformatic \ **S**\ ervices."

WAVES is a dedicated Django based web application to ease bioinformatic tools integration through web interfaces in
order to provide the scientific community with bioinformatic services.

It is aimed to help you easily present, publish and give access on the web to any bioinformatic tool.


Features
--------

- Create and manage your services execution over platform such as Galaxy, DRMAA clusters (SGE), Direct script execution, API calls to other services, remote calls to other platforms via ssh, etc.
- Easily presents these tools in a nice frontend based on Bootstrap3, Bootstrap4 and soon Material Design
- Follow and manage remote REST API access to your service platform
- Manage user's access to your services

.. note::
    - WAVES main component is WAVES-core.
    - WAVES-Galaxy is another component. It is a WAVES adapter to interact with Galaxy instances.
    - WAVES-demo is a custom version of WAVES-core for demo purpose only.

Side projects
-------------

- WAVES-galaxy adapter `<https://www.github.com/lirmm/waves-galaxy>`_
- WAVES-demo project `<https://www.github.com/lirmm/waves-demo>`_


Installation
------------

- You can use WAVES-core as a stand alone application.
- WAVES-core comply to standard reusable project layout for Django. So you may include it as a dependency in your own django project
- Complete documentation available on `readthedocs <https://waves-core.readthedocs.io>`_


Support
-------

If you are having issues, (or just want to say hello): we have a mailing list located at: waves@lirmm.fr


-- UPDATE to 1.7.xx from 1.6.xxx --
-----------------------------------

If migrating from a version 1.6.x to any 1.7.x, you must patch you database encrypted password to a more reliable
encrypted technology (https://github.com/pyca/cryptography). This script must be run once and only once !
To migrate your data please do the following:
- retrieve the latest version 1.7.x
- stop any running service  
- save your database first
- once the new version is installed, run `manage.py migrate_keys`
- if you don't have any error message: your keys are now more secured ! 