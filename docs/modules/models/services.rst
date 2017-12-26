.. _service-label:

Services
========

Services are the main entry point for WAVEs application, managed by :ref:`service-manager-label`.

    .. py:currentmodule:: waves.wcore.models.services
    .. autoclass:: waves.wcore.models.services.Service
        :members:
        :inherited-members:
        :show-inheritance:

Services may be accessed from multiple 'submissions'

    .. autoclass:: waves.wcore.models.services.Submission
        :members:
        :show-inheritance:

.. _service-inputs-label:

Submission Inputs
-----------------

Base class for service inputs shared information
    .. autoclass:: waves.wcore.models.inputs.BooleanParam
    .. autoclass:: waves.wcore.models.inputs.DecimalParam
    .. autoclass:: waves.wcore.models.inputs.FileInput
    .. autoclass:: waves.wcore.models.inputs.IntegerParam
    .. autoclass:: waves.wcore.models.inputs.TextParam

.. _service-outputs-label:

Submission Outputs
------------------
Submission description defines expected outputs

    .. autoclass:: waves.wcore.models.services.SubmissionOutput
        :members:


Submission ExitCode
-------------------

Submission description defines expected exitcode

    .. autoclass:: waves.wcore.models.services.SubmissionExitCode
        :members:

.. _service-samples-label:

Input Samples:
--------------

Services may provide sample data for their submissions

    .. autoclass:: waves.wcore.models.inputs.FileInputSample
        :members:
        :undoc-members:
        :show-inheritance:

    .. autoclass:: waves.wcore.models.inputs.SampleDepParam
        :members:
        :undoc-members:
        :show-inheritance: