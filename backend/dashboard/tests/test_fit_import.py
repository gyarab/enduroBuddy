from __future__ import annotations

from ._fit_import_base import DashboardFitImportBase
from ._fit_import_flow_cases import DashboardFitImportFlowCases
from ._fit_import_garmin_cases import DashboardFitImportGarminCases
from ._fit_import_rendering_cases import DashboardFitImportRenderingCases


class DashboardFitImportTests(
    DashboardFitImportFlowCases,
    DashboardFitImportRenderingCases,
    DashboardFitImportGarminCases,
    DashboardFitImportBase,
):
    pass
