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


0. Install your django application
----------------------------------

    To create a Django project, have a look at `Django tutorial <https://docs.djangoproject.com/en/1.11/intro/tutorial01/>`_
    GET a WAVES web-app online following the next few steps, WAVES can run on Apache, Nginx with uWSGI

    .. note::
        In order to install WAVES you need:
            - python 2.7.X (WAVES is not yet compatible with python3)
            - pip package manager

        For production, a web server:
                - `Apache <https://httpd.apache.org/>`_
                - `NGINX <https://nginx.org/>`_


1. Install WAVES-core package
-----------------------------

    1.1. Install waves package:

        ``pip install waves-core``

        If you want to install the latest version
            ``pip install -e git+https://github.com/lirmm/waves-core.git#egg=waves-core``

    1.2. Go to your Django settings file (usually settings.py) and add required dependencies to your INSTALLED_APPS:

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
            'polymorphic',
            ...
            'waves.wcore',
            'crispy_forms',
            'rest_framework',
            ...
        ]

    1.3. Include the services urls in your project urls.py::

        url(r'^waves/', include('waves.wcore.urls', namespace='wcore'))
        url(r'^waves/api/', include('waves.wcore.api.urls', namespace='wapi'))

    1.4. Create your database::

        python manage.py makemigrations
        python manage.py migrate
        python manage.py check

