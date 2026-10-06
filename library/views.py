import hashlib
from datetime import timedelta
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import F
from django.shortcuts import render
from django.utils import timezone
from .models import LoginAttempt
from .permissions import school_required

class LimitedLoginView(LoginView):
    template_name='registration/login.html'
    def key(self):
        return hashlib.sha256(self.request.POST.get('username','').strip().casefold().encode()).hexdigest()
    def post(self,request,*args,**kwargs):
        old=LoginAttempt.objects.filter(key=self.key(),window_start__gt=timezone.now()-timedelta(minutes=15),failures__gte=5).exists()
        if old:
            form=self.get_form();form.add_error(None,'Кӯшишҳо зиёданд. Баъди 15 дақиқа такрор кунед.')
            return self.render_to_response(self.get_context_data(form=form),status=429)
        return super().post(request,*args,**kwargs)
    def form_invalid(self,form):
        with transaction.atomic():
            attempt,_=LoginAttempt.objects.select_for_update().get_or_create(key=self.key(),defaults={'window_start':timezone.now()})
            if attempt.window_start<timezone.now()-timedelta(minutes=15):
                attempt.window_start=timezone.now();attempt.failures=0
            attempt.failures+=1;attempt.save()
        return super().form_invalid(form)
    def form_valid(self,form):
        LoginAttempt.objects.filter(key=self.key()).delete()
        return super().form_valid(form)
