from api.models import ReportExport as BaseReportExport, SavedReport as BaseSavedReport


class SavedReport(BaseSavedReport):
    class Meta:
        proxy = True
        verbose_name = 'Saved report'
        verbose_name_plural = 'Saved reports'


class ReportExport(BaseReportExport):
    class Meta:
        proxy = True
        verbose_name = 'Report export'
        verbose_name_plural = 'Report exports'
