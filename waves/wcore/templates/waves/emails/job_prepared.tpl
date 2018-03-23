-------------------------------------------------------------------------------------------
[WAVES-NOTIFICATION] - Job submission for '{{ job.service }}' - your job is {{ job.get_status_display|lower }}
-------------------------------------------------------------------------------------------

Your job "{{ job.title }}" is now prepared for running

    List of inputs data
    {% for out in job.input_files %}
        - {{  out.name }} {{ out.link }}
    {% endfor %}

    Job will run with following parameters:
    {% for out in job.input_params %}
        - {{  out.name }}
    {% endfor %}

