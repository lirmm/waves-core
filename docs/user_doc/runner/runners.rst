.. _runner-admin-label:

Runner Configuration
====================

Runners are the entry point where you can setup your actual running configuration

Runner list
-----------

    List all currently registered runner available on your WAVES platform, you may add / remove (cautionnaly) any one of
    default setup included in WAVES

    .. figure:: backoffice/runner-list.png
        :align: center
        :width: 90%

Runner Details
--------------

    On detailed Runner page, configure some descriptive parameters

    - *Runner name* : the displayed runner name user in front / back-office for reference
    - *Description* : this will appear on front end on job / services generated pages
    - *Availability* : Set whether this runner is enabled for launching jobs

        .. CAUTION::
            When you disable a 'live' runner used in services, it automatically disable related service from anywhere !

    - *Implementation Class* : select inlist one of your defined 'actual' runner adaptor, feel free to add any from source !
    - *Update init params* : When checked, upon save, all related services configuration is reset to parameters

        .. CAUTION::
            These services are now is stage 'Draft'

    .. figure:: backoffice/runner-detail.png
        :align: center
        :width: 90%

    .. TIP::
        If you want to setup default values for implementing class initial params, save and edit again your runner, you will see
        params updated down your admin interface

        .. figure:: backoffice/runner-param.png
            :align: center
            :width: 90%

