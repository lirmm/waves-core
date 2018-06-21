Job queue management
====================


Job List
--------

Jobs are listed in first screen when you click on **jobs** link in main backoffice view.

    .. figure:: backoffice/job-list.png
        :align: center
        :width: 90%
        :figclass: thumbnail

Job Details
-----------
On this view you may want to see job online, see associated service, or cancel the job (if possible).


General Information
    You can check general information about job here, such as :

    - Title
    - Associated Service
    - Current Status
    - Creation and last update date
    - Associated client if job has been submitted by a registered user
    - Email where notifications are sent
    - Generated unique slug for this Job
    - Current runner where job is actually run
    - Generated command line where applicable for runner

    .. figure:: backoffice/job-general.png
        :align: center
        :width: 90%
        :figclass: thumbnail

Job History
    Retrieve here all logged events for this job, including administration message (may describe errors).

    .. figure:: backoffice/job-history.png
        :align: center
        :width: 90%
        :figclass: thumbnail

Job Inputs
    Designated inputs for this job

    .. figure:: backoffice/job-inputs.png
        :align: center
        :width: 90%
        :figclass: thumbnail

Job Outputs
    Current expected outputs

    .. figure:: backoffice/job-outputs.png
        :align: center
        :width: 90%
        :figclass: thumbnail
