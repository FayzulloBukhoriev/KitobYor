from django.urls import path
from . import views
urlpatterns=[
 path('students/',views.Students.as_view()),
 path('editions/',views.Editions.as_view()),
 path('editions/<int:pk>/intake/',views.StockIntake.as_view()),
 path('editions/<int:pk>/tariff/',views.TariffSet.as_view()),
 path('kits/',views.Kits.as_view()),
 path('issues/preview/',views.Preview.as_view()),
 path('issues/confirm/',views.IssueConfirm.as_view()),
 path('invoices/',views.Invoices.as_view()),
 path('invoices/<int:pk>/',views.InvoiceDetail.as_view()),
 path('invoices/<int:pk>/payments/',views.Payments.as_view()),
 path('loans/<int:pk>/returns/',views.Returns.as_view()),
]
