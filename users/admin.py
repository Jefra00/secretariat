from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'role', 'telephone', 'pays', 'verified', 'statut', 'date_inscription'
    )

    list_filter = (
        'role', 'verified', 'statut', 'langue', 'pays'
    )

    search_fields = (
        'username', 'email', 'first_name', 'last_name', 'telephone'
    )

    ordering = ('-date_inscription',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {
            'fields': (
                'first_name', 'last_name', 'email',
                'telephone', 'adresse', 'bio', 'avatar'
            )
        }),
        ('Rôle et statut', {
            'fields': (
                'role', 'verified', 'statut', 'langue', 'pays'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_inscription', 'last_activity')
        }),
    )

    readonly_fields = ('date_inscription', 'last_activity', 'last_login')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'first_name', 'last_name', 'role'
            ),
        }),
    )