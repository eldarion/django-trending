from django.contrib import admin

from trending.models import DailyViewSummary, ViewLog


admin.site.register(DailyViewSummary)
admin.site.register(ViewLog)