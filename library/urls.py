from django.urls import path,include
from . import views
urlpatterns=[path('',views.dashboard,name='dashboard'),path('api/v1/',include('library.api.urls'))]
