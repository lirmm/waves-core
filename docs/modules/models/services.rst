.. _service-label:

Services
========

Services are the main entry point for WAVEs application, managed by :ref:`service-manager-label`.

    .. autoclass:: waves.core.models.services.Service
        :members:
        :show-inheritance:

Services may be accessed from multiple 'submissions'

    .. autoclass:: waves.core.models.submissions.Submission
        :members:
        :show-inheritance:

.. _service-inputs-label:

Submission Inputs
-----------------

Base class for service inputs shared information
        .. autoclass:: waves.core.models.inputs.AParam
            :members:
            :show-inheritance:

.. _service-outputs-label:

Submission Outputs:
-------------------
Submission description defines expected outputs

    .. autoclass:: waves.core.models.submissions.SubmissionOutput
        :members:

Submission Outputs:
-------------------
Submission description defines expected exitcode

    .. autoclass:: waves.core.models.submissions.SubmissionOutput
        :members:




.. _service-samples-label:

Input Samples
-------------

Services may provide sample data for their submissions

    .. autoclass:: waves.core.models.samples.FileInputSample
        :members:
        :undoc-members:
        :show-inheritance:

    .. autoclass:: waves.core.models.samples.SampleDepParam
        :members:
        :undoc-members:
        :show-inheritance: