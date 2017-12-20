.. _dev-guide:

===============
Developer Guide
===============


Create your own adaptor
-----------------------

Under construction

Overriding Services and Submissions
-----------------------------------

WAVES offers the possibility to extends two main objects declared in application,
in case these does not fit perfectly developers expectations:
Service and Submission can therefore be updated with your specific needs.

An example is available in WAVES- demo project.

Just extends base classes in your models classes:
- “waves.wcore.models.services.BaseService”,
- “waves.wcore.models.services.BaseSubmission”

Then declare your classes as new “Service” and “Submission” models in your Django settings.py as follow

WCORE_SERVICE_MODEL = 'yourapp.YourOverriddenServiceClass'
WCORE_SUBMISSION_MODEL = ‘yourapp.YourOverriddenSubmissionClass’


Overriding WAVES templates
--------------------------

Under construction

Overriding API entries
----------------------

Under construction

Overriding Forms create template packs
--------------------------------------

Under construction
