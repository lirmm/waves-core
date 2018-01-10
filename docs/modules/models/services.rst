.. _service-label:

Services
========

Services are the main entry point for WAVEs application, managed by :ref:`service-manager-label`.

    .. autoclass:: waves.wcore.models.services.Service
        :members:
        :inherited-members:
        :show-inheritance:

Submissions
===========

Services may be accessed from multiple 'submissions'

    .. autoclass:: waves.wcore.models.services.Submission
        :members:
        :inherited-members:
        :show-inheritance:

.. _service-inputs-label:

Submission Inputs
-----------------

Classes for service's submission inputs information

Booleans
^^^^^^^^
    .. autoclass:: waves.wcore.models.inputs.BooleanParam
        :inherited-members:

Decimals
^^^^^^^^
    .. autoclass:: waves.wcore.models.inputs.DecimalParam
        :inherited-members:

Files
^^^^^
    .. autoclass:: waves.wcore.models.inputs.FileInput
        :inherited-members:

Integers
^^^^^^^^
    .. autoclass:: waves.wcore.models.inputs.IntegerParam
        :inherited-members:

Text Inputs
^^^^^^^^^^^
    .. autoclass:: waves.wcore.models.inputs.TextParam
        :inherited-members:

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