.. _installation-label:


Installation
============

    .. WARNING::
        To run WAVES, it's strongly recommended that you setup a dedicated user, because WAVES run with
        saga-python, and this module need to create some directories you might not be able to create (.radical and .saga)
        with another user (such as www-data)

    .. warning::
        WAVES was initially developed with Python 2.7 and Django 1.11
        and is currently not tested on latest version (Python 3 and Django 2.0).

    .. note::
        In order to install WAVES you need:
            - python 2.7.X (WAVES is not yet compatible with python3)
            - pip package manager

You can install WAVES-core either as a stand alone application, or inside any existing Django project

1. Install WAVES-core inside existing Django project
----------------------------------------------------

    To create a Django project, have a look at `Django tutorial <https://docs.djangoproject.com/en/1.11/intro/tutorial01/>`_

    1.0. Setup a virtualenv for your project

        ``virtualenv ~/.venv/[waves_env]``


    1.1. Install waves package:

        Use pip to install waves-core as thrid party package.

        ``pip install waves-core``

        If you want to install the latest development version (at your own risk :-))
            ``pip install -e git+https://github.com/lirmm/waves-core.git#egg=waves-core``

    1.2. Activate WAVES-core in Django settings, add required dependencies to your INSTALLED_APPS:

    WAVES-core application has minimum dependencies to:

    - `Django polymorphic <https://django-polymorphic.readthedocs.io/>`_
    - `Crispy forms <http://django-crispy-forms.readthedocs.io>`_
    - `Django Rest Framework <http://www.django-rest-framework.org/>`_

    Optionally, WAVES-core can use:

    - `Django CkEditor <https://github.com/django-ckeditor/django-ckeditor>`_
    - `Django Admin sortable 2 <http://django-admin-sortable2.readthedocs.io>`_
    - `Django Jet <http://jet.geex-arts.com/>`_

    You should at least find these apps installed in your project::

        INSTALLED_APPS = [
            'polymorphic', # mandatory
            ...
            'waves.wcore', # mandatory
            'crispy_forms', # mandatory
            'rest_framework', # mandatory
            ...
            'rest_framework.authtoken', # optional see http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication
            'corsheaders', # optional see https://github.com/ottoyiu/django-cors-headers
            'adminsortable2', # optional see https://django-admin-sortable2.readthedocs.io
            ...
        ]

    1.3. Include the services urls in your project urls.py::

        url(r'^waves/', include('waves.wcore.urls', namespace='wcore'))
        url(r'^waves/api/', include('waves.wcore.api.urls', namespace='wapi'))

    1.4. Create your database::

        python manage.py makemigrations wcore
        python manage.py migrate wcore
        python manage.py check

    1.5. Extra configuration:

    Depending on your needs, you might want to expose WAVES API to any registered user, if so have a look at:
    - see `Corsheader <https://github.com/ottoyiu/django-cors-headers>`_ to allow cross-origin Resource Sharing

    Some WAVES-core API services requires authentication:
    - see `DRF authentication <http://www.django-rest-framework.org/api-guide/authentication>`_ for authenticating methods API POST calls

    .. note::
        WAVES-core allows simple "token" authentication with standard token Authentication processes, to use it simply add
        'rest_framework.authtoken' in INSTALLED_APPS.

        Each authenticated api service need a valid Authorization header as explained here:
        http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication


2. Install WAVES-core as stand alone application

    2.1. Clone repository:

    Current version is |version|

    .. code-block:: bash

        user@host:$ git clone https://github.com/lirmm/waves-core.git [your_app]
        user@host:$ cd [your_app]
        user@host:~your_app$ git checkout tags/v[VERSION]

    2.2. Install dependencies:


    .. code-block:: bash

        user@host:~your_app$ virtualenv .venv
        user@host:~your_app$ source .venv/bin/activate
        (.venv) user@host:~your_app$ pip install -r requirements.txt

    You might need other dependencies if working with other DB layout than sqlite.

    2.3. Install database

    .. code-block:: bash

        (.venv) user@host:~your_app$ ./manage.py check
        (.venv) user@host:~your_app$ ./manage.py makemigrations wcore
        (.venv) user@host:~your_app$ ./manage.py migrate
        (.venv) user@host:~your_app$ ./manage.py createsuperuser


    2.4. If everything is ok:

    You can start your test server like this:

    .. code-block:: bash

        (.venv) user@host:~your_app$ ./manage.py waves queue start
        (.venv) user@host:~your_app$ ./manage.py runserver

3. To configure WEB for production:

    Please refer to `Django Official documentation <https://docs.djangoproject.com/fr/1.11/howto/deployment/>`_
