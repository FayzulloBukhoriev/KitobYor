from django.contrib import admin
from .models import School,Membership,AuditEvent,StockMovement,Invoice,Payment
admin.site.register(School)
admin.site.register(Membership)
class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self,r): return False
    def has_change_permission(self,r,obj=None): return False
    def has_delete_permission(self,r,obj=None): return False
for model in [AuditEvent,StockMovement,Invoice,Payment]: admin.site.register(model,ReadOnlyAdmin)
admin.site.site_header='KitobYor · Идоракунии марказӣ'
