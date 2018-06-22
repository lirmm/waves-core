.. _waves-dev-guide:

=======================
WAVES Deveveloper Guide
=======================

Job Workflow
============

 .. figure:: images/job_workflow.png
        :width: 90%
        :align: center
        :figclass: thumbnail

        Classic Job execution workflow in WAVES-core


.. _extending-adaptor-label:

Create a WAVES-core adaptor
===========================

The base abstract class "JobAdaptor" defines methods to manage a simple job execution workflow.

First of all, override class ``__init__(self, *args, **kwargs)`` method if you need more params to create your Adaptor instance.
Then accordingly, override ``init_params(self)`` property function in order to return a dictionary for each entry expected in constructor.
It allows WAVES-core administration module to automatically load these entries in computing infrastructure :ref:`configuration parameters panel <environment-set-up>`.

    .. seealso::
        Look at source to find what to override and how it's already made in WAVES-core adaptors :ref:`Sources <adaptor-base-class-label>`

    * ``connect(self)``: Process the connection to the calculation device

        - Override ``_connect(self)`` method to implement your own connection protocol implementation

    * ``disconnect(self)``: Disconnect process from calculation device, may do some cleaning on device as well

        - Override ``_disconnect(self)`` method to realize cleaning on disconnect

    * ``prepare_job(self, job)``: Job state must be "Created", this method is in charge of preparing job, job is now "Prepared"

        - Override ``_prepare_job(self, job)`` to prepare job for your needs

            - Create job expected output files
            - Possibly upload files to remote platform

    * ``run_job(self, job)``: Job state must be "Prepared", actually create job on computing infrastructure, queue it for execution Job is now "Queued".

        - Override ``_run_job(self, job)`` to launch job execution on your dedicated platform

    .. note::
        The job execution workflow is then relayed to computing infrastructure, WAVES does not intend to be a workflow manager, supervisor.

    * ``job_status(self, job)``: Job current status check, map WAVES-core status map to computing infra. Return current Job.

        - Override ``_job_status(self, job)`` to retrieve job status from your platform (should return an item mapped in _state_map

    * ``job_results(self, job)``: Once job is "remotely" finished, get (possibly download) the expected outputs from computing infra to job working dir.

        - Override ``_job_results(self, job)`` to retrieve job outputs and get them back to WAVES-core platform

    * ``job_run_details(self, job)``: Upon results retrieval, get job stats on computing infrastructure

        - Override ``_job_run_details(self, job)`` to create a JobRunDetail object with your job stats

    * ``cancel_job(self, job)``: Try to cancel job on computing infrastructure

        - Override ``_cancel_job(self, job)`` to perform job cancellation on your platform

Each of the preceding method definition calls an inner method prefixed by '_' (_connect, _disconnect, etc. ) meant to be overridden in subclasses to actually process the action
on computing infrastructure. Furthermore, an adaptor need to declare a simple dictionary mapping computing infrastructure job states code to WAVES-core ones :
_states_map = {}.

WAVES-core uses constant for defining its jobs states as follows (available in waves.wcore.adaptors.const.py)

Job states constants
--------------------
        +---------------+------------+
        | Python const  |  Int value |
        +===============+============+
        | JOB_UNDEFINED |   -1       |
        +---------------+------------+
        | JOB_CREATED   |    0       |
        +---------------+------------+
        | JOB_PREPARED  |    1       |
        +---------------+------------+
        | JOB_QUEUED    |    2       |
        +---------------+------------+
        | JOB_RUNNING   |    3       |
        +---------------+------------+
        | JOB_SUSPENDED |    4       |
        +---------------+------------+
        | JOB_COMPLETED |    5       |
        +---------------+------------+
        | JOB_TERMINATED|    6       |
        +---------------+------------+
        | JOB_CANCELLED |    7       |
        +---------------+------------+
        | JOB_WARNING   |    8       |
        +---------------+------------+
        | JOB_ERROR     |    9       |
        +---------------+------------+

Class diagram overview
----------------------

    .. figure:: images/adaptors.png
        :width: 90%
        :align: center
        :figclass: thumbnail

        Adaptor class diagram overview

Currently classes tree implemented in WAVES-core can communicate with a large number of calculation devices, locally or remotely over SSH:

    * Sun Grid Engine - now Oracle Grid Engine
    * SLURM
    * PBS
    * CONDOR
    * PBS Pro
    * LSF
    * TORQUE

This is made possible thanks to  `SAGA Python <http://saga-python.readthedocs.io/en/latest/>`_ that implements the `GFD <https://www.ogf.org/documents/GFD.90.pdf>`_
interface specification.

.. note::
    A specific adaptor has been created in dedicated app to communicate with a `galaxy <https://waves-galaxy-adaptors.readthedocs.io/>`_ server


Overriding Services and Submissions
===================================

Some WAVES-core models classes are easily extensible. WAVES-core offers the possibility to extends two main objects declared in application,
in case these does not fit perfectly developers expectations:

* Service: waves.wcore.models.services.BaseService
* Submission: waves.wcore.models.services.BaseSubmission


To extend these models, simply declare your classes in your models, and then declare your classes as new “Service” and “Submission” models in your Django settings.py as follow:

WCORE_SERVICE_MODEL = 'yourapp.YourOverriddenServiceClass'
WCORE_SUBMISSION_MODEL = ‘yourapp.YourOverriddenSubmissionClass’

Remember to always use shortcut methods "get_service_model" and "get_submission_model" to gain access to model instances.

.. note::
    An example of this capability is available in `WAVES-demo <https://github.com/lirmm/waves-demo/blob/master/src/demo/models.py>`_ project.
    This example override Service class to add classification with a standard category association, and adds some Meta information to services.

Overriding WAVES templates
==========================

Well, as WAVES-core complies to Django reusable app standard, it's pretty straigthforward to extend WAVES-core base templates following Django documentation,
each submission configuration results in a dedicated form and a dedicated REST API entry.
Thanks to Django framework, rendering forms inside other pages is made easy with standard templatetags dedicated to WAVES-core generated forms.

Related urls
------------

======================================  =======================================================
URI                                     Description
======================================  =======================================================
/waves/services/                        List all available services
/waves/services/{service_app_name}/     Display Service details
/waves/services/{service_app_name}/new  Create a job (access to available submission(s) form(s)
/waves/jobs/{slug}/                     View job details
/waves/jobs/inputs/{slug}/[?export=1]   View Input file online / Download file
/waves/jobs/outputs/{slug}/[?export=1]  View Output file online / Download file
======================================  =======================================================


WAVES-core defines the following base templates

Services
--------

======================================  =======================================================
Template path                           Description
======================================  =======================================================
~/waves/services/base.html              Base template used for block definition
~/waves/services/service_list.html      List all available services defined in WAVES apps
~/waves/services/service_details.html   Main service page defined in WAVES apps
~/waves/services/service_form.html      Page to display service's related submissions forms
~/waves/services/file.html              Display a line for a file input / output for service
======================================  =======================================================


.. hint::
    WAVES-core allows override for a single service / submission template, following naming convention for templates, simply create a new template
    in your templates subdir 'waves/override/' (service_app_name is the app_short_code defined in BO for the service):

    * For service: service_[service_app_name]_detail.html
    * For submission: submission_[service_app_name]_form.html

Jobs
----
========================================  ======================================================================
Template path                             Description
========================================  ======================================================================
~/waves/jobs/job_list.html                Display a list of user's jobs
~/waves/jobs/parts/job_list_element.html  A list element template for a job in list
~/waves/jobs/job_detail.html              Job detail page, list submitted inputs parameters and expected outputs
========================================  ======================================================================


.. seealso::
    `<https://docs.djangoproject.com/en/1.11/howto/overriding-templates/>`_


Overriding API entries
======================

WAVES-core heavily use `Django Rest Framework <http://www.django-rest-framework.org/>`_ to create api entries for service.

“GET” endpoints are by default accessible without login, POST method (create a job) needs a registered user. You can change this in DRF configuration.

Following standard url patterns definition you may override defaults defined hereafter:

Service endpoints
-----------------

======  =============================================================================   ===================================================================================
METHOD  URI                                                                             Description
======  =============================================================================   ===================================================================================
GET     /waves/api/services                                                             List all available services
GET     /waves/api/services/{service_app_name}                                          Retrieve service details
GET     /waves/api/services/{service_app_name}/form                                     Retrieve service forms (for all submissions)
GET     /waves/api/services/{service_app_name}/jobs                                     Retrieves services Jobs (only for logged in users)
GET     /waves/api/services/{service_app_name}/submissions                              List all available submissions for this service
GET     /waves/api/services/{service_app_name}/submissions/{submission_app_name}        Get Service submission detailed information (inputs, parameters, expected outputs)
POST    /waves/api/services/{service_app_name}/submissions/{submission_app_name}/jobs   Create a new job from submitted inputs
GET     /waves/api/services/{service_app_name}/submissions/{submission_app_name}/jobs   List all users jobs for this submission
GET     /waves/api/services/{service_app_name}/submissions/{submission_app_name}/form   Service to load submission form as raw html
======  =============================================================================   ===================================================================================


Jobs endpoints
--------------

======  ==============================  ==========================================================================================
METHOD  URI                             Description
======  ==============================  ==========================================================================================
GET     /waves/api/jobs                 List all available user’s jobs
POST    /waves/api/jobs/{slug}/cancel   Try to cancel running job on remote calculation device if possible. Mark job as cancelled.
DELETE  /waves/api/jobs/{slug}          Try to cancel job on remote calculation device if possible. Delete Job from DB
GET     /waves/api/jobs/{slug}          Detailed job information
GET     /waves/api/jobs/{slug}/history  Job events  history
GET     /waves/api/jobs/{slug}/status   Job current status
GET     /waves/api/jobs/{slug}/inputs   List job submitted inputs
GET     /waves/api/jobs/{slug}/outputs  List job outputs, associated with direct link to associated file
======  ==============================  ==========================================================================================


Overriding forms create template packs
======================================

Under construction
