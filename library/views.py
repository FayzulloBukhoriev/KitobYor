import hashlib
from datetime import timedelta
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import F,Q
from django.shortcuts import render
from django.utils import timezone
from .models import LoginAttempt
from .permissions import school_required

class LimitedLoginView(LoginView):
    template_name='registration/login.html'
    def key(self):
        return hashlib.sha256(self.request.POST.get('username','').strip().casefold().encode()).hexdigest()
    def ip_key(self):
        from django.conf import settings
        trusted=getattr(settings,'SECURE_PROXY_SSL_HEADER',None) is not None
        address=self.request.META.get('HTTP_X_REAL_IP') if trusted else None
        address=address or self.request.META.get('REMOTE_ADDR','unknown')
        return hashlib.sha256(('ip:'+address).encode()).hexdigest()
    def post(self,request,*args,**kwargs):
        old=LoginAttempt.objects.filter(Q(key=self.key(),failures__gte=5)|Q(key=self.ip_key(),failures__gte=50),window_start__gt=timezone.now()-timedelta(minutes=15)).exists()
        if old:
            form=self.get_form();form.add_error(None,'Кӯшишҳо зиёданд. Баъди 15 дақиқа такрор кунед.')
            return self.render_to_response(self.get_context_data(form=form),status=429)
        return super().post(request,*args,**kwargs)
    def form_invalid(self,form):
        with transaction.atomic():
            for key in sorted([self.key(),self.ip_key()]):
                attempt,_=LoginAttempt.objects.select_for_update().get_or_create(key=key,defaults={'window_start':timezone.now()})
                if attempt.window_start<timezone.now()-timedelta(minutes=15):
                    attempt.window_start=timezone.now();attempt.failures=0
                attempt.failures=min(attempt.failures+1,1000);attempt.save()
        return super().form_invalid(form)
    def form_valid(self,form):
        LoginAttempt.objects.filter(key=self.key()).delete()
        return super().form_valid(form)

from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from django.urls import reverse_lazy

from .forms import SchoolPasswordChangeForm

class AccountPasswordChange(PasswordChangeView):
    form_class=SchoolPasswordChangeForm
    template_name='registration/password_change.html'
    success_url=reverse_lazy('account')
    def form_valid(self,form):
        messages.success(self.request,'Рамзи нав сабт шуд.')
        return super().form_valid(form)
    def get_context_data(self,**kwargs):
        context=super().get_context_data(**kwargs)
        context.update(title='Иваз кардани рамз',active='account')
        membership=getattr(self.request.user,'membership',None)
        context['can_library']=bool(membership and membership.role in ('admin','librarian'))
        return context
