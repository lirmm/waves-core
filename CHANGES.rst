Version 1.1.6 - 2017-12-30
--------------------------

    - Removed: waves.front, merged back inside wcore
    - [Admin] Added: admin urls directly in related Wcore ModelAdmins
    - [Models] Added: fields authors and citation to Service model
    - [API] Added: Add Job cancel and delete services
    - [Models] Removed: removed fields api_on and web_on in Service model
    - [Jobs] Changed: JobInconsistentState treatment in job workflow
    - [Models] Added: 'topics' and 'operations' property for reading EDAMS ontology data in Service templates
    - [Adaptors] Moved: Saga common processes in dedicated class SagaAdaptor

Version 1.1.5 - 2017-11-30
--------------------------

    - Corrected: .type property on JobInput
    - Added: filter_fields on job ViewSet
    - Added: job instance attribute in JobSubmissionViewSet (create_job)
    - Added: submission label in Job detail api results

Version 1.1.4 - 2017-10-24
--------------------------

    - Corrected fixture loading conflict with signals on api_name duplicate check


Version 1.1.3 - 2017-10-18
--------------------------

    - Corrected bugs in Galaxy tool import
    - Changed importer API to resolve problem with included runner / adaptor params
    - added SRV_IMPORT_LOG_LEVEL to configuration

Version 1.1.2 - 2017-09-30
--------------------------

    - Added pip package (waves-core) - updated 2017/10/03
    - Added changeLog in documentation
    - Added BinaryFile upload:
        - Association with Runners / Services / Submission for command lines
    - Added standard Django inclusion tags to display Submissions forms templates
        - {% load waves_tags %} => {% submission_form %}, {% service_inc "css" %}, {% service_inc "js" %}
        - Templates directories structure in order to use all available crispy templates packs
        - Check crispy configuration on startup
        - Dynamic includes tags for related css and js from cdnjs
    - Simplify overrides for front templates
    - Cleaning code to PEP8 standards
    - Updated install documentation
    - Make Submission model swappable as well
    - Added Popup Edit for Submission params Model Admin
    - Added quick and dirty solution to override services templates for specific service
    - Corrected bugs
        - JsPopupInlines for Django-jet admin layout
        - workflow Runner tests
        - daemon command failed with SQLite DB (depends now on daemons package `̀https://pypi.python.org/pypi/daemons/1.3.0`)


Version 1.1.1 - 2017-07-30
--------------------------

    - Corrected many bugs from beta
    - api v2
    - decoupled front / core templates
    - Make Service model swappable (for overriding capabilities in other apps)
    - Removed un-mandatory dependencies (django-constance, grappelli, django-jet) - added compat files


Version 1.1.0 - 2017-03-30
--------------------------

Initial Beta version

