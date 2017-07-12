Installation
============

GET a WAVES web-app online following the next few steps, WAVES can run on Apache, Nginx with uWSGI


0. Prerequisites
----------------
    .. WARNING::
        To run WAVES, it's strongly recommended that you setup a dedicated user, because WAVES run with
        saga-python, and this module need to create some directories you might not be able to create (.radical and .saga)
        with another user (such as www-data)

    .. note::
        In order to install WAVES you will need:
            - python 2.7.X (WAVES should be compatible with python 3.5 but not fully tested)
            - pip package manager
            - A web server: `Apache <https://httpd.apache.org/>`_ or `NGINX <https://nginx.org/>`_
            - A database backend (Mysql or Postgres) but WAVES basically runs out-of-the-box with a sqlite DB

1. Install WAVES
----------------

    1.1. Install waves package (strongly recommended to do so in a
       dedicated virtualenv):

       ``pip install -e git+https://github.com/lirmm/waves-core.git#egg=waves``

    1.2. Add "waves" to your INSTALLED_APPS settings, minimum apps are as follow ::

        INSTALLED_APPS = [
            'polymorphic',
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'waves',
            'crispy_forms',
            'rest_framework',
            ...
        ]

    1.3. Include the services urls in your project urls.py::

            url(r'^waves/', include('waves.core.urls', namespace='waves')),

            Alternativly you can use only parts waves urls configuration you need:

                url(r'^admin/waves/', include('waves.core.urls.waves_admin_url', namespace='waves')),
                url(r'^my-api/', include('waves.core.urls.waves_api_url', namespace='waves')),
                url(r'^waves/', include('waves.core.urls.front_url', namespace='waves'))

    1.4. Run ``python manage.py makemigrations`` to update database models.

    1.5. Run ``python manage.py migrate`` to import sample data if you wish

    1.6. Run ``python manage.py check`` to check installation
