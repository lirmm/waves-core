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

    .. seealso::

        * `RabbitMQ Installation <http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#rabbitmq>`_
        * `Rabbit MQ Celery broker configuration <http://docs.celeryproject.org/en/latest/getting-started/brokers/rabbitmq.html#broker-rabbitmq>`_
        * `Celery Django <http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#using-celery-with-django>`_

1. Install WAVES
----------------

    1.0. Configure RabbitMQ message broker::

        $sudo rabbitmqctl add_user waves [mypassword]
        $sudo rabbitmqctl add_vhost [yourHost]
        $sudo rabbitmqctl set_user_tags waves [mytag]
        $sudo rabbitmqctl set_permissions -p [yourHost] waves ".*" ".*" ".*"

    1.1. Install waves package (strongly recommended to do so in a  dedicated virtualenv):

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

    1.3. Include the services urls in your project urls.py::

        url(r'^waves/', include('waves.wcore.urls', namespace='waves')),

    1.4. Create your database::

        python manage.py makemigrations
        python manage.py migrate
        python manage.py check
