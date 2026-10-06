from django.conf import settings
def school_context(request):
    membership = getattr(request.user, 'membership', None) if request.user.is_authenticated else None
    return {'membership':membership,'school':membership.school if membership else None,'demo_mode':getattr(settings,'DEMO_MODE',False)}
