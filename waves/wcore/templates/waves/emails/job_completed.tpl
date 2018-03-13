------------------------------------------------------------------------------------------------------------------
[WAVES-NOTIFICATION] - Job completed for '{{ job.service.name }}' - your job is {{ job.get_status_display|lower }}
------------------------------------------------------------------------------------------------------------------

Your job {{ job.title }} is {{ job.get_status_display|lower }}
    {% for inp in job.input_files %}
        - {{  inp.name }}: {{ inp.link }}
    {% endfor %}


    {% if job.results_available %}
    Its outputs are:
    {% for out in job.output_files_exists %}
        - {{ out.name }}: {{ out.link }}
    {% endfor %}
    {% endif %}

Retrieve all your job details at {{ job.link }}

Thanxs for using WAVES ! {{ contact }}
