WAVES python samples code
=========================


.. note::
These examples use coreapi package functionalities
    see: http://www.coreapi.org/


Interact with services
----------------------

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


Authenticate with token:
------------------------

Some WAVES API entries required to be authenticated (jobs list, job details, job submission)

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


Create a job:
-------------

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


