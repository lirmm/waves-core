.. _service-admin-label:

=======================
Services administration
=======================

How to configure a service in WAVES application

Service list
============
 This is landing page when you click on 'Services' Links in Admin home page, you can see current list of services
 registered on your platform

    .. figure:: backoffice/service-list.png
        :width: 90%
        :align: center
        :figclass: thumbnail

 Click on **+ Add Service** to create a new service

Service details
===============

General options
---------------

    .. figure:: backoffice/service-general.png
        :width: 90%
        :align: center
        :figclass: thumbnail

        Main general options for a WAVES service

    - **Service name**: Service name displayed on front and api
    - **Created by**: Only superuser can change this value, this is set by default to current user
    - **Version**: Current version for your service (no relation with actual software version)
    - **Status**: Current online status for this service, upon creation, it's automatically set to 'Draft'

        - *DRAFT*: Service is under configuration, by now, it is not intended to be available to anyone except the service’s creator.
        - *STAFF*: Service configuration is finished (inputs / outputs / run configuration), it then can be open to the others team users, i.e back-office users
        - *REGISTERED*: Service is fully configured, tested, but restricted to registered users (those who have an Django activated account)
        - *RESTRICTED*: Service is intended to be used by specific registered users. WAVES-core allows to set up these users by specifically selected them in service configuration  back-office service page.
        - *PUBLIC*: Service is open to any user who visit the website, still, access to REST API is subjected to user registration prior to use its capabilities.

    - **App short code**: this value is used for generating urls and api entry points, for service, this value must be unique

        .. CAUTION::
            Modify *app short code* attribute when service is online can break api clients

    - **Short description**: Short description text about what service is about (not displayed on front but only on api)
    - **Execution environment**: Execution configuration (see :ref:`runner-admin-label` administration)
    - **Binary file**: You can upload here the executable file which will be used for execution

Access management
-----------------

    .. figure:: backoffice/service-access.png
        :width: 90%
        :align: center
        :figclass: thumbnail

        Access panel presents granted given to Service

    - **Notify results**: Whether or not users are notified when job is terminated
    - **Access restriction**: When service's status is 'RESTRICTED', you may set up allowed users for this service

Service details
-----------------

    .. figure:: backoffice/service-detail.png
        :width: 90%
        :align: center
        :figclass: thumbnail

        Detailed informations for your service

    - **Created on**: Creation date (automatic)
    - **Last update**: Update date (automatic)
    - **Description**: A longer description about your service, may include some HTML content (you may then add CKEditor as a dependency for your project)
    - **Edams topics**: A list of comma separated edam topics reference
    - **Edams operations**: A list of comma separated edam operation reference
    - **Remote service tool id**: Some remote computing platform may add a required id, once your service is deployed (automatic)


Service execution configuration
-------------------------------
    .. figure:: backoffice/service-runner.png
        :width: 90%
        :align: center
        :figclass: thumbnail

    You can set run configuration values for each expected parameters for service execution, one is always required: 'command'


    .. hint::
        You can prevent subsequent submission(s) to override a value in their own configuration administration page, by checking related 'Prevent override' checkbox



