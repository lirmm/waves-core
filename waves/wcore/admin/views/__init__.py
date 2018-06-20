"""
Admin specific views
"""

from waves.wcore.admin.views.job_tool import JobCancelView, JobRerunView
from waves.wcore.admin.views.json_view import JSONDetailView, JSONView
from waves.wcore.admin.views.runner_tool import RunnerExportView, RunnerImportToolView, RunnerTestConnectionView
from waves.wcore.admin.views.service_tool import ServiceDuplicateView, ServiceExportView, ServiceParamImportView, ServiceTestConnectionView, \
    ServicePreviewForm, ServiceModalPreview
