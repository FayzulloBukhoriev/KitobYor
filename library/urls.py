from django.urls import path,include
from . import ui
from .views import AccountPasswordChange
urlpatterns=[
    path('sms/',ui.sms_messages,name='sms_messages'),
    path('account/',ui.account,name='account'),
    path('account/password/',AccountPasswordChange.as_view(),name='password_change'),
    path('account/audit/',ui.audit_log,name='audit_log'),
    path('',ui.dashboard,name='dashboard'),
    path('students/',ui.students,name='students'),
    path('students/new/',ui.student_form,name='student_new'),
    path('students/<int:pk>/edit/',ui.student_form,name='student_edit'),
    path('students/import/',ui.student_import,name='student_import'),
    path('students/template/',ui.import_template,name='import_template'),
    path('inventory/',ui.inventory,name='inventory'),
    path('inventory/new/',ui.catalog_form,name='catalog_new'),
    path('inventory/<int:pk>/',ui.catalog_form,name='edition_detail'),
    path('kits/',ui.kits,name='kits'),
    path('kits/new/',ui.kit_form,name='kit_new'),
    path('issue/',ui.issue,name='issue'),
    path('invoices/',ui.invoices,name='invoices'),
    path('invoices/<int:pk>/',ui.invoice_detail,name='invoice_detail'),
    path('reports/',ui.reports,name='reports'),
    path('reports/export/',ui.export,name='export'),
    path('api/v1/',include('library.api.urls')),
]
