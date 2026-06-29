from django.contrib.gis import admin as gis_admin
from .models import Boutique


@gis_admin.register(Boutique)
class BoutiqueAdmin(gis_admin.GISModelAdmin):
    list_display  = ['nom', 'user', 'ville', 'commune', 'type_commerce', 'actif', 'cree_le']
    list_filter   = ['actif', 'type_commerce', 'ville']
    search_fields = ['nom', 'user__first_name', 'user__telephone', 'adresse_exacte']
    list_editable = ['actif']
    raw_id_fields = ['user', 'ville', 'commune', 'quartier', 'marche']
    fieldsets = (
        ('Identité', {'fields': ('user', 'nom', 'telephone', 'description', 'logo')}),
        ('Localisation', {'fields': ('ville', 'commune', 'quartier', 'marche', 'type_commerce', 'adresse_exacte', 'position')}),
        ('Statut', {'fields': ('actif', 'raison_blocage')}),
    )
