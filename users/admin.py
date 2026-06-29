from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, VendeurProfile, Paiement

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


@admin.register(VendeurProfile)
class VendeurProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'section', 'nom_commercial', 'actif', 'date_creation')
    list_filter   = ('section', 'actif')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'nom_commercial')
    raw_id_fields = ('user',)
    ordering      = ('-date_creation',)


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display  = ('pk', 'client', 'section', 'montant_total', 'methode', 'statut', 'cree_le')
    list_filter   = ('section', 'statut', 'methode', 'mode_livraison')
    search_fields = ('client__first_name', 'client__last_name', 'client__email', 'reference_externe')
    date_hierarchy = 'cree_le'
    ordering      = ('-cree_le',)
    readonly_fields = ('cree_le', 'mis_a_jour_le')