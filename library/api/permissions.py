from rest_framework.permissions import BasePermission, SAFE_METHODS
from library.models import Membership
class SchoolPermission(BasePermission):
    message='Ҳисоб ба мактаб пайваст нест ё ваколат надорад.'
    def has_permission(self,request,view):
        if not request.user.is_authenticated: return False
        try: member=Membership.objects.select_related('school').get(user=request.user)
        except Membership.DoesNotExist: return False
        request.school=member.school
        request.member=member
        if request.method in SAFE_METHODS: return True
        return member.role in getattr(view,'write_roles',('admin','librarian'))
