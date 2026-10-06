from django.contrib import admin
from django.urls import include,path
from django.contrib.auth.views import LogoutView
from library.views import LimitedLoginView
urlpatterns = [path('admin/',admin.site.urls),path('login/',LimitedLoginView.as_view(),name='login'),path('logout/',LogoutView.as_view(),name='logout'),path('',include('library.urls'))]
