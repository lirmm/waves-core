------------------------------------------------------------------------------------------------------------------
[WAVES-NOTIFICATION] - Job completed for '{{ job.service }}' - your job is {{ job.get_status_display|lower }}
------------------------------------------------------------------------------------------------------------------

Your job "{{ job.title }}" is completed: "{{ job.get_status_display|lower }}"

Retrieve all your job details at

{{ job.link }}
