WAVES API python samples code
=========================


.. note::
These examples use coreapi package functionalities
    see: http://www.coreapi.org/


Interact with services
----------------------

You can interact with a WAVES API instance by using `coreapi <http://www.coreapi.org/>`_.
These examples show how to get a list of services or a service details, a submission or inputs and outputs expected.

.. code-block:: python

    from coreapi import Client, auth
    from coreapi.codecs import CoreJSONCodec, JSONCodec

    decoders = [JSONCodec(), CoreJSONCodec()]
    # Create a client client codecs
    client = Client(decoders=decoders)
    document = client.get('http://waves.demo.atgc-montpellier.fr/waves/api/schema')
    # get service list - replace with actual waves-api urls
    serviceList = client.action(document, ['services', 'list'])
    print(serviceList)
    # get service details
    serviceDetails = client.action(document, ["services", "read"], params={'service_app_name': 'sample_service'})
    print(serviceDetails['name'])
    # get service submissions
    submissions = client.action(document, ["services", "submissions_list"],
                                params={"service_app_name": 'sample_service'})
    # get first submission details
    sub_details = client.action(document, ["services", "submission"],
                                params={"service_app_name": "sample_service",
                                        "submission_app_name": "default"})
    # get inputs / outputs
    expected_inputs = sub_details['inputs']
    print(expected_inputs)
    expected_outputs = sub_details['outputs']
    print(expected_outputs)


Authenticate with token
-----------------------

Some WAVES API entries require to be authenticated (jobs list, job details, job submission). Token are given by the administrator.

.. code-block:: python

    client = Client(decoders=decoders,
                auth=auth.TokenAuthentication(
                    token="6241961ef45e4bbe7bb01a05f938ed9f0f2a3926",
                    scheme="Token"))
    document = client.get('http://waves.demo.atgc-montpellier.fr/waves/api/schema')
    # list jobs
    # get job list
    job_list = client.action(document, ['jobs', 'list'])
    print("job_list", job_list)
    if (len(job_list) > 0):
        job_details = client.action(document, ['jobs', 'read'], params={'unique_id': job_list[0]['slug']})
        print(job_details['title'])
        print(job_details['created'])
        print(job_details['updated'])

Integrate a WAVES service form
------------------------------

You've got a website and you want your visitors could submit jobs? The better way for this is to add in your website using API.
Here, you're supposed to know there is a service named "sample_service" defined on demo WAVES instance (as you see in serviceList above).

.. code-block:: python

    from coreapi import Client, auth
    from coreapi.codecs import CoreJSONCodec, JSONCodec, TextCodec
    decoders = [JSONCodec(), CoreJSONCodec(), TextCodec()]
    client = Client(decoders=decoders)
    document = client.get('http://waves.demo.atgc-montpellier.fr/waves/api/schema')
    wavesform = client.action(document, ['services', 'form'], params={"service_app_name": 'sample_service'}, validate=False, encoding='multipart/form-data')

Now, you just render this form into your template (ex. in a django tpl).

.. warning::
    Don't forget to add forms.css and services.js from your waves instance as in this sample.

.. code-block:: django

    {% block head %}
       {% addtoblock "waves_forms_css" %} <link rel="stylesheet" href="http://waves.demo.atgc-montpellier.fr/static/waves/css/forms.css">{% endaddtoblock %}
    {% endblock %}

    {% block main %}
    <!-- Import the web form as is -->
    {{ wavesform|safe }}
    {% endblock main %}

    {% block footer %}
        {% addtoblock "js" %}
            <script src="http://waves.demo.atgc-montpellier.fr/static/waves/js/services.js"></script>
        {% endaddtoblock %}
    {% endblock footer %}

Create a job
------------

It's also possible to create a job directly from your client interface. Here we see how to create a job called "Job Name" which use a "default" submission of "sample_service" service.
Inputs are defined by expected inputs of the "sample_service". Be aware, "validate=false" is required to submit a file

.. code-block:: python

    # submit a job
    from coreapi.utils import File
    from os.path import join, dirname

    with open(join(dirname(__file__), "test.fasta"), 'r') as f:
        inputs = {
            "text_input": "This is text input",
            "input_file": File("test.fasta", f)
        }
        client.action(document, ["services", "submissions", "jobs", "create"],
                      params={
                          **inputs,
                          "title": "Job Name",
                          "service_app_name": "sample_service",
                          "submission_app_name": "default"
                      }, validate=False, encoding='multipart/form-data')
    job_list = client.action(document, ['jobs', 'list'])
    print(job_list)

