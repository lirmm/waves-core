Administrator Guide
===================

Services are defined by administrators, then configured to allow users to gain access to submission web forms and REST api entry points.

Everything is made simple with help of dedicated back office entries.
There, administrators firstly describe services in term of name, description, authors, citation links, edams ontology topics and operations,
execution environment configuration (see “Execution adaptor”).

Once service main data are setup, administrators can configure precisely related submission to setup inputs, execution parameters, outputs, etc…

Upon service publication, it is automatically available in two ways: standard web pages including html forms, and a REST API
service entry point to be remotely accessed from a distant application.

Some more configuration can be made to tune user’s access rights, execution parameters etc. those are further detailed in this document:

    .. toctree::
       :maxdepth: 3
       :numbered:

       runner/runners
       service/services
       service/submissions
       job/jobs


.. figure:: waves-admin.png
    :width: 90%
    :align: center
    :figclass: thumbnail

    Django classic backoffice landing page for WAVES-core module

