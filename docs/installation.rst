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
        In order to install WAVES you need:
            - python 2.7.X (WAVES is not yet compatible with python3)
            - pip package manager
            - Django Application set up (use `Waves-demo <https://github.com/lirmm/waves-demo>`_ project if you don't have one )
            - Web server: `Apache <https://httpd.apache.org/>`_ or `NGINX <https://nginx.org/>`_
            - Message broker : we won't force you but Waves is tested with Celery and RabbitMQ

1. Install WAVES
----------------

    1.1. Install waves package:

        ``pip install -e git+https://github.com/lirmm/waves-core.git#egg=waves``

    1.2. Add "waves" to your INSTALLED_APPS settings, minimum apps are as follow ::

        INSTALLED_APPS = [
            'polymorphic',
            ...
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            ...
            'waves.wcore',
            ...
            'crispy_forms',
            'rest_framework',
            ...
        ]

    1.3. Include the services urls in your project urls.py:

        ``url(r'^wcore/', include('waves.wcore.urls', namespace='wcore'))``

        1.3.1 If you need standard front pages:

            ``url(r'^waves/', include('waves.front.urls', namespace='wfront')),``

        1.3.2 If you need api:

            ``url(r'^api/', include('waves.wcore.api.urls', namespace='wapi'))``


    1.4. Create your database::

        python manage.py makemigrations
        python manage.py migrate
        python manage.py check
