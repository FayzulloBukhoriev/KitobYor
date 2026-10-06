from django.contrib import admin
from django.urls import include,path
from django.contrib.auth.views import LogoutView
from library.views import LimitedLoginView
from library.health import health
from django.contrib.admin.forms import AdminAuthenticationForm

def admin_login(request,extra_context=None):
    context={**admin.site.each_context(request),'title':'Ворид шудан','app_path':request.get_full_path(),**(extra_context or {})}
    return LimitedLoginView.as_view(template_name='admin/login.html',authentication_form=AdminAuthenticationForm,extra_context=context)(request)

admin.site.login=admin_login
urlpatterns = [path('healthz/',health,name='health'),path('admin/',admin.site.urls),path('login/',LimitedLoginView.as_view(),name='login'),path('logout/',LogoutView.as_view(),name='logout'),path('',include('library.urls'))]
