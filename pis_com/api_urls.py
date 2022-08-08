from django.urls import path


from pis_com.api_views import *

urlpatterns = [
    path("api/sales/daily/", daily_sales_api,name='daily_sales_api'),
    # re_path(r'^sales/weekly/$', WeeklySalesAPI.as_view(),name='weekly_sales_api'),
    # re_path(r'^sales/monthly/$', MonthlySalesAPI.as_view(),name='monthly_sales_api'),
]
