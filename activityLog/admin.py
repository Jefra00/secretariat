from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'categorie', 'action', 'ip_address', 'succes', 'date_action')
    list_filter = ('categorie', 'succes', 'date_action')
    search_fields = ('user__username', 'action', 'description', 'objet_concerne')
    readonly_fields = ('user', 'categorie', 'action', 'description', 'ip_address', 'user_agent', 'date_action', 'succes', 'objet_concerne')
    ordering = ('-date_action',)

    def has_add_permission(self, request):
        return False  # ✅ empêche la création manuelle de logs dans l’admin
