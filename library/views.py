from django.http import HttpResponse
from django.contrib.auth.views import LoginView
class LimitedLoginView(LoginView):
    template_name='registration/login.html'
def dashboard(request):return HttpResponse('KitobYor: development in progress')
