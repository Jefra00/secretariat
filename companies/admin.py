from django.contrib import admin
from .models import Company, CompanyService


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('nom', 'secteur', 'email_contact', 'telephone', 'actif', 'note_globale', 'nombre_services', 'nombre_commandes')
    list_filter = ('actif', 'secteur')
    search_fields = ('nom', 'email_contact', 'telephone', 'site_web')
    readonly_fields = ('date_inscription', 'nombre_commandes', 'note_globale')
    ordering = ('nom',)


@admin.register(CompanyService)
class CompanyServiceAdmin(admin.ModelAdmin):
    list_display = ('company', 'service', 'forfait', 'tarif_final', 'actif', 'renouvellement_auto', 'date_creation')
    list_filter = ('actif', 'renouvellement_auto')
    search_fields = ('company__nom', 'service__nom', 'forfait')
    readonly_fields = ('date_creation',)
