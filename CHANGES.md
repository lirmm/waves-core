CHANGELOG
=========

Version 2.0.0 - 2020-02-25
--------------------------

- [Major] - Some major updates / breaking changes alongside moving to 
    - Python 3 
    - Django 2.XXX
    - Radical saga 1.0.1
- [Major] - Remove swappable for Service/Submission (obsolete use case and work around described [here])
- [Major] - Following packages out of waves.core namespace:
    - api
    - compat
    - ..
- [Major] - removed code for WAVES api v1


Version 1.6.7 - 2020-01-08
--------------------------

- [Mails] - Ignore settings for admin email - force sending
- [Services Templates] - Integrate JSON-LD into services displayed pages. 


Version 1.6.6 - 2019-09-12
--------------------------

- [Commands] - Fix Error in command to migrate to new encryption lib
- [Queue] - Added Celry/Redis option to process job queue 

Version 1.6.5 - 2019-06-15
--------------------------

- [Encryption] - MAJOR update on cryptography library in use within WAVES - https://github.com/pyca/cryptography see README
- [Commands] - Removed temporarly wqueue processing - issues with remaining processes 


Version 1.6.x - 2018-03-10
----------------------------

- [Layout] - Corrected missing directories
- [ignore] - Added ignored files
- [Bug] - Corrected display in BO for passwords
- [USERS] - Added API USER class, unifying authentication, url redirection dedicated to REST Api users 
    - Added multi-site association allow returning site url prefix for jobs urls
    - Test if job.client user has a 'site' property, in such case, retrieve domain name to generate Job / JobOutputs link
- [LOGGING] JobLogging: degraded mode, output to 'waves.errors' logger
- [Service list] Corrected: list services fails when services are not all public (1.1.9.2).
- [Admin JobList] Corrected: remove wrong filter on jobAdmin queryset (1.1.9.3)
- [API ServiceList] Added: added service_app_name to returned json
- [API Submission] Changed: api_name => submission_app_name in returned json
- [API ServiceList] Changed: changed format for service submission list
 

Version 1.5.x - 2018-02-10
----------------------------

- [JS] Corrected: event association on add new input in submission form
- [Daemon] Corrected: log any fatal exception during job processing in job file
- [Admin Service] Corrected: key error when editing service on 'created_by'
- [Admin Service] Corrected: inline popup on add ExitCode
- [Settings] Added: check for WAVES directories access rights
- [File Permission] Changed to 775/664 job created dirs/files.

Version 1.3 - 2018-02-07
--------------------------

- [Updated] - shared logging behaviour in Jobs / Importer
- [Corrected] - service import method

Version 1.2 - 2018-01-31
--------------------------

- [waves.front] Removed: waves.front, merged back inside wcore
- [Admin] Added: admin urls directly in related Wcore ModelAdmins
- [Models] Added: fields authors and citation to Service model
- [API] Added: Add Job cancel and delete services
- [Models] Removed: removed fields api_on and web_on in Service model
- [Jobs] Changed: JobInconsistentState treatment in job workflow
- [Models] Added: 'topics' and 'operations' property for reading EDAMS ontology data in Service templates
- [Adapters] Moved: Saga common processes in dedicated class SagaAdaptor
- [FileInput] Added: Configuration for enabling/disabling copy/paste form element
- [Docs]: Introduce Administrator guide / Developer guide
- [Api]: Introduce standard token authentication for API form integration
- [Db]: Removed migrations files - causing fails migrate with overridden Submission model - added makemigration upon install

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
- Changed importer API to resolve problem with included runner / adapter params
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

