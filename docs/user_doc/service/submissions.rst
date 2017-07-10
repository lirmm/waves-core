.. _service-submission-label:

Services Submission Administration
==================================

Each service may be accessed by multiple ways i.e submissions

1. Submission
    For each services, you can setup multiple ways to submit a job, for example if your service may have a 'standard'
    inputs list, and some 'experts' one for another type of jobs. Inputs in each submission configuration are not
    necessarily correlated.
    For each 'Submission configuration', you can add, remove, order possible inputs.

    Service Inputs:
        You may add as many input as required for your service on this page.

        Each Input needs:

        - *Label* : nice display for your input in forms
        - *Type* : which determine the way parameters are setup in command line (as an option, a positional param, named param etc.)
        - *Name* : this is the actual parameter name used in command line or in job submission
        - *Control Type* : This field setup the type of the input (file, text, int, bool, list, float)
        - *List* : Display (for Control type list only!): how you want to display list items (radio / chekboxes / select)
        - *Submitted by user* : if checked, this input will be shown in JobSubmission webpage, and on API, if not, Input needs a default value (i.e for some reason, you set a kind of 'constant' for your job submission)
        - *Type format* : depending on 'Control Type', you may set here allowed values for the fields (this is not an option for 'list' typed element)
        - *Default* : default value for your input
        - *Description* : short help text displayed in both api and Web pages
        - *Multiple* : checked means that this input can hold multiple values, typically when you want to submit multiple files for the same input for your script
        - *Mandatory* : is checked, form and api calls cannot be submitted if no value is set (or default in case your input is not submitted by user)

        .. figure:: backoffice/submission-params.png
            :width: 90%
            :align: center

    Related Inputs
        Sometime, your services may setup dependencies between inputs, for exemple, if you setup a service which use
        DNA or Protein substitution models, you may want to change these models upon selection of type of data.

        So, to help you, WAVES allows to add "Related input" to a service input (down Service Input form part), where
        you can set exactly the same values as for a normal input, **plus** :

        - *When condition* : Activation value (from 'parent' Input), if parent is a list, correspond to selected value

        .. TIP::
            First save with "Save and Continue editing" to have a select from possible values in 'When condition' field

        .. ATTENTION::
            Related inputs can't be 'mandatory', because their submission is dependent on another one which potentially is not set

    Service Outputs
        Along with your service inputs, you want to setup all expected outputs for each jobs.

        A service output is defined by:

        - *Name* : the displayed name for your output
        - *From Input* : sometime, script uses some inputs values to setup outputs file names.
        - *File Name* : output file name, may contains a '%s' pattern referencing associated input value for creating file name
        - *Description* : show on form a little help message about content displayed with output
        - *Output Valuated from Input* :
            if *From input* is checked, you must setup associated input, one per defined submission, failing to do this will aim to not working service

        .. figure:: backoffice/submission-output.png
            :width: 90%
            :align: center

    Service ExitCodes
        Here you can define:

        - *Exit Code Value* : expected exit code (should be an int value)
        - *Message* : Associated message to display
        - *Associated job Status* : whether or not to change job final status if exit code occurred

        .. figure:: backoffice/submission-exitcode.png
            :width: 90%
            :align: center

