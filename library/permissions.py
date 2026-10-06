from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .models import Membership

def school_required(*roles):
    def deco(view):
        @wraps(view)
        @login_required
        def wrapped(request,*args,**kwargs):
            try: member=Membership.objects.select_related('school').get(user=request.user)
            except Membership.DoesNotExist:raise PermissionDenied('Ҳисоби шумо ба мактаб пайваст нест.')
            if roles and member.role not in roles:raise PermissionDenied('Барои ин амал ваколат надоред.')
            request.school=member.school
            request.member=member
            return view(request,*args,**kwargs)
        return wrapped
    return deco
