Version 1.1.2 - 2017-09-30
--------------------------

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

