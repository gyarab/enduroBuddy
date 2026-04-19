from __future__ import annotations

from ._fit_import_base import DashboardFitImportBase
from ._fit_import_flow_cases import DashboardFitImportFlowCases
from ._fit_import_garmin_cases import DashboardFitImportGarminCases


class DashboardFitImportTests(
    DashboardFitImportFlowCases,
    DashboardFitImportGarminCases,
    DashboardFitImportBase,
):
    pass
