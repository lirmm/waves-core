.. _dev-guide:

===============
Developer Guide
===============

Definitions
===========

Computing infrastructure
-------------------------
It is composed of computationally dedicated hardware and the software components required to operate it, including calculation management programs (distributed resource management systems, Galaxy,...).

Adaptor
-------
It is a Django module allowing WAVES to communicate with a specified computing infrastructure.  For each computing infrastructure, WAVES needs a dedicated adaptor.

Service
-------
A service is a bioinformatic tool available online through the http protocol. It can be accessed from a web form or through  REST API calls.

Submission
----------
Many bioinformatic tools provide several distinct usages. For instance, a program can be run using the command-line interface or by providing a configuration file. Otherwise, the same tool can be run on different computing infrastructures. A submission is the combination of a usage and a computing infrastructure. Thus, a service can rely on different submissions.

Job
---
A job stands for a command with parameters. It is run on a dedicated computing infrastructure. It may require inputs such as files. It generates outputs: exit code, standard output and standard error, and possibly result files. A job is run each time a submission is invoked by a service.

User
----
A user is a client which accesses services. It can be a real person using  its web browser or a software using the REST API.

Administrator
-------------
An administrator is a privileged user with granted access to the WAVES back office. He manages services, submissions, adaptors and jobs.


Documentation
=============

.. toctree::
    :maxdepth: 3
    :numbered:

    waves_dev_doc
    api_user_doc
    sample_code

