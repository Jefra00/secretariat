from django.contrib import admin
from django.utils.html import format_html
from .models import Marche, Vendeur, Categorie, Couleur, Produit, ProduitImage


@admin.register(Couleur)
class CouleurAdmin(admin.ModelAdmin):
    list_display  = ['apercu', 'nom', 'code_hex', 'description']
    search_fields = ['nom']

    def apercu(self, obj):
        if obj.code_hex:
            return format_html(
                '<div style="width:22px;height:22px;border-radius:50%;'
                'background:{};border:1px solid #ccc;display:inline-block"></div>',
                obj.code_hex
            )
        return '—'
    apercu.short_description = ''


class ProduitImageInline(admin.TabularInline):
    model       = ProduitImage
    extra       = 1
    fields      = ['image', 'couleur', 'ordre', 'principale', 'description']
    readonly_fields = ['apercu_image']

    def apercu_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;border-radius:6px">', obj.image.url)
        return '—'
    apercu_image.short_description = 'Aperçu'


@admin.register(ProduitImage)
class ProduitImageAdmin(admin.ModelAdmin):
    list_display  = ['apercu_image', 'produit', 'couleur', 'ordre', 'principale', 'date_ajout']
    list_filter   = ['principale', 'couleur']
    search_fields = ['produit__nom', 'description']
    raw_id_fields = ['produit']
    list_editable = ['ordre', 'principale']

    def apercu_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:48px;border-radius:6px">', obj.image.url)
        return '—'
    apercu_image.short_description = 'Image'


@admin.register(Marche)
class MarcheAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'ville', 'commune', 'actif']
    list_filter   = ['ville', 'actif']
    search_fields = ['nom']


@admin.register(Vendeur)
class VendeurAdmin(admin.ModelAdmin):
    list_display  = ['nom_boutique', 'type_commerce', 'ville', 'verified', 'actif', 'date_inscription']
    list_filter   = ['type_commerce', 'ville', 'verified', 'actif']
    search_fields = ['nom_boutique', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user', 'marche']


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display        = ['emoji', 'nom', 'slug', 'ordre']
    prepopulated_fields = {'slug': ('nom',)}


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'categorie', 'prix', 'devise', 'unite', 'nb_images', 'disponibilite', 'stock', 'vendeur']
    list_filter   = ['categorie', 'disponibilite', 'devise', 'ville']
    search_fields = ['nom', 'description', 'vendeur__nom_boutique']
    raw_id_fields = ['vendeur', 'marche', 'categorie']
    inlines       = [ProduitImageInline]

    def nb_images(self, obj):
        n = obj.images.count()
        return f'{n} image{"s" if n > 1 else ""}' if n else '—'
    nb_images.short_description = 'Images'
