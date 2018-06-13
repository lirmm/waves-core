WAVES python samples code
=========================


.. note::
These examples use coreapi package functionalities
    see: http://www.coreapi.org/


Interact with services
----------------------

.. code-block:: python

    from coreapi import Client, auth
    from coreapi.codecs import JSONCodec

    decoders = [JSONCodec()]
    # Setup client codecs
    client = Client(decoders=self.decoders)
    # get service list - replace with actual waves-api urls
    serviceList = client.get('http://waves.demo.atgc-montpellier.fr/waves/api/services')
    # get service details
    serviceDetails = client.get(serviceList[0]['url'])
    # get service submissions
    submissions = serviceList[0]['submissions'])
    # get first submission details
    sub_details = client.get(submissions[0]['url'])
    # get intputs / outputs
    expected_inputs = sub_details['inputs']
    expected_inputs = sub_details['outputs']


Authenticate with token:
------------------------

.. code-block:: python

    client = Client(
        auth=auth.TokenAuthentication(token=app_key, scheme="Token"),
        decoders=self.decoders)

Create a job:
-------------

.. code-block:: python

    # load swagger api description
    document = client.get("http://waves.demo.atgc-montpellier.fr/waves/api/swagger")
    inputs = {"input_1" : "value1"}
    client.action(document, ["services", "submissions_jobs_create"],
                    params={
                        "inputs": inputs,
                        "name": "Job Name",
                        "service_app_name": service_app_name,
                        "submission_app_name": submission_app_name
                    })

