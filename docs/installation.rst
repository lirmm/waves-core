.. _installation-label:

============
Installation
============

    .. WARNING::
        To run WAVES-core, it's strongly recommended that you setup a dedicated user, because WAVES-core run with
        saga-python, and this module need to create some directories you might not be able to create (.radical and .saga)
        with another user (such as www-data)

    .. warning::
        WAVES-core was initially developed with Python 2.7 and Django 1.11
        and is currently not tested on latest version (Python 3 and Django 2.0).

You can install WAVES-core either as a stand alone application, or inside any existing Django project

0. Prerequisites
----------------
    .. note::
        In order to install WAVES-core you will need:
            - python 2.7.X (WAVES-core is not yet compatible with python 3.5)
            - pip package manager ($sudo apt install python-pip python-dev build-essential)
            - A web server: `Apache <https://httpd.apache.org/>`_ or `NGINX <https://nginx.org/>`_
            - A database backend (Mysql or Postgres) but by default WAVES-core runs with sqlite


WAVES is developed with `Django <https://www.djangoproject.com/>`_. You may need to know a little about `it <https://docs.djangoproject.com/en/1.11/>`_.



1. Install WAVES-core as stand alone application
------------------------------------------------

    1.1. Clone repository:

    Current version is |version| (|release|)

    .. code-block:: bash

        user@host:$ git clone https://github.com/lirmm/waves-core.git [your_app]
        user@host:$ cd [your_app]

    .. note::
        To checkout a particular version:

        user@host:~your_app$ git checkout tags/[VERSION]

    1.2. Install dependencies:

    .. code-block:: bash

        user@host:~your_app$ virtualenv .venv
        user@host:~your_app$ source .venv/bin/activate
        (.venv) user@host:~your_app$ pip install -r requirements.txt

    You might need other dependencies if working with other DB layout than sqlite.

    1.3. Install database:

    .. code-block:: bash

        (.venv) user@host:~your_app$ ./manage.py check
        (.venv) user@host:~your_app$ ./manage.py makemigrations wcore (may only display "No changes detected in app 'wcore'")
        (.venv) user@host:~your_app$ ./manage.py migrate
        (.venv) user@host:~your_app$ ./manage.py createsuperuser (then follow instructions)


    1.4. If everything is ok:

    You can start your test server and job queue like this:

    .. code-block:: bash

        (.venv) user@host:~your_app$ ./manage.py wqueue start
        (.venv) user@host:~your_app$ ./manage.py runserver

    Go to http://127.0.0.1:8000/admin to setup your services
    WAVES-core comes with default front pages visible at http://127.0.0.1:8000


2. Install WAVES-core inside existing Django project
----------------------------------------------------

    To create a Django project, have a look at `Django tutorial <https://docs.djangoproject.com/en/2.11/intro/tutorial01/>`_

    .. seealso::

        WAVES-core is a reusable app see: https://docs.djangoproject.com/en/1.11/intro/reusable-apps/#your-project-and-your-reusable-app


    2.0. Setup a virtualenv for your project:

        ``virtualenv ~/.venv/[waves_env]``


    2.1. Install waves package:

        Use pip to install waves-core as third party package.

        ``pip install waves-core``

        If you want to install the latest development version (at your own risk :-))
            ``pip install -e git+https://github.com/lirmm/waves-core.git#egg=waves-core``

    2.2. Activate WAVES-core in settings:

    WAVES-core application has minimum dependencies to:

    - `Django polymorphic <https://django-polymorphic.readthedocs.io/>`_
    - `Crispy forms <http://django-crispy-forms.readthedocs.io>`_
    - `Django Rest Framework <http://www.django-rest-framework.org/>`_

    Optionally, WAVES-core can use:

    - `Django CkEditor <https://github.com/django-ckeditor/django-ckeditor>`_
    - `Django Admin sortable 2 <http://django-admin-sortable2.readthedocs.io>`_
    - `Django Jet <http://jet.geex-arts.com/>`_

    Add required dependencies to your INSTALLED_APPS, you should at least find these in your project::

        INSTALLED_APPS = [
            'polymorphic', # mandatory
            ...
            'waves.wcore', # mandatory
            'waves.authentication', # mandatory if API token access needed
            'crispy_forms', # mandatory
            'rest_framework', # mandatory
            ...
            'rest_framework.authtoken', # optional see http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication
            'corsheaders', # optional see https://github.com/ottoyiu/django-cors-headers
            'adminsortable2', # optional see https://django-admin-sortable2.readthedocs.io
            ...
        ]

    2.3. Include the services urls in your project urls.py::

        url(r'^waves/', include('waves.wcore.urls', namespace='wcore'))
        url(r'^waves/api/', include('waves.wcore.api.urls', namespace='wapi'))

    2.4. Create your database::

        python manage.py makemigrations wcore
        python manage.py migrate wcore
        python manage.py check

    2.5. Extra configuration:

    Depending on your needs, you might want to expose WAVES API to any registered user, if so have a look at: `Corsheader <https://github.com/ottoyiu/django-cors-headers>`_ to allow cross-origin Resource Sharing

    Some WAVES-core API services requires authentication, see `DRF authentication <http://www.django-rest-framework.org/api-guide/authentication>`_ for authenticating methods API POST calls

    .. note::
        WAVES-core allows simple "api_key" authentication with standard Token Authentication processes, to use it simply add
        'waves.authentication' in INSTALLED_APPS.

        This then allow to call WAVES API services with a api_key:
            - with Authorization token header
            - with GET / POST parameter with api_key value.

        Each authenticated api service need a valid Authorization header as explained here:
        http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication

        To use this service with apache in mod_wsgi: please mind to enable "WSGIPassAuthorization On" parameter in conf

3. Use other than SqlLite default DB layer
------------------------------------------

    You may need to install the Python and MySQL development headers and libraries like so:

        - sudo apt-get install python-dev default-libmysqlclient-dev # Debian / Ubuntu
        - sudo yum install python-devel mysql-devel # Red Hat / CentOS
        - brew install mysql-connector-c # macOS (Homebrew) (Currently, it has bug. See below)

    On Windows, there are binary wheels you can install without MySQLConnector/C or MSVC.

    Then install pip mysql package in your virtualenv:

        ``pip install mysqlclient``

    .. seealso::

        https://docs.djangoproject.com/en/1.11/ref/databases/