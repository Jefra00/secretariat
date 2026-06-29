from django.contrib.gis import admin
from .models import Ville, Commune, Quartier


@admin.register(Ville)
class VilleAdmin(admin.GISModelAdmin):
    list_display = ['nom', 'pays', 'a_position', 'a_contour', 'actif', 'created_at']
    list_filter  = ['actif', 'pays']
    search_fields = ['nom']

    def a_position(self, obj): return '✓' if obj.position else '—'
    a_position.short_description = 'Point'

    def a_contour(self, obj): return '✓' if obj.contour else '—'
    a_contour.short_description = 'Contour'


@admin.register(Commune)
class CommuneAdmin(admin.GISModelAdmin):
    list_display  = ['nom', 'ville', 'a_position', 'a_contour', 'actif']
    list_filter   = ['actif', 'ville']
    search_fields = ['nom', 'ville__nom']
    autocomplete_fields = ['ville']

    def a_position(self, obj): return '✓' if obj.position else '—'
    a_position.short_description = 'Point'

    def a_contour(self, obj): return '✓' if obj.contour else '—'
    a_contour.short_description = 'Contour'


@admin.register(Quartier)
class QuartierAdmin(admin.GISModelAdmin):
    list_display  = ['nom', 'commune', 'a_position', 'a_contour', 'actif']
    list_filter   = ['actif', 'commune__ville']
    search_fields = ['nom', 'commune__nom']

    def a_position(self, obj): return '✓' if obj.position else '—'
    a_position.short_description = 'Point'

    def a_contour(self, obj): return '✓' if obj.contour else '—'
    a_contour.short_description = 'Contour'
