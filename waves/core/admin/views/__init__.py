"""
Admin specific views
"""

from waves.core.admin.views.job_tool import JobCancelView, JobRerunView
from waves.core.admin.views.json_view import JSONDetailView, JSONView
from waves.core.admin.views.runner_tool import RunnerExportView, RunnerImportToolView, RunnerTestConnectionView
from waves.core.admin.views.service_tool import ServiceDuplicateView, ServiceExportView, ServiceParamImportView, \
    ServiceTestConnectionView, ServicePreviewForm, ServiceModalPreview
