from django.contrib import admin
from django.utils.html import format_html
from .models import CategorieQuincaillerie, ProduitQuincaillerie, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'couleur', 'principale', 'ordre', 'description')
    readonly_fields = ('date_ajout',)


@admin.register(CategorieQuincaillerie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('icone', 'nom', 'categorie_parent')
    list_display_links = ('nom',)
    search_fields = ('nom',)


@admin.register(ProduitQuincaillerie)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'marque', 'categorie', 'prix_display', 'statut_badge', 'etat', 'quantite_stock', 'ville')
    list_filter = ('statut', 'etat', 'categorie', 'livraison_disponible', 'ville')
    search_fields = ('nom', 'reference', 'marque', 'description')
    inlines = [ProductImageInline]
    readonly_fields = ('date_creation', 'date_modification')
    fieldsets = (
        ('Identification', {
            'fields': ('boutique', 'categorie', 'nom', 'reference', 'marque', 'etat')
        }),
        ('Tarification', {
            'fields': ('prix', 'prix_promotionnel', 'unite')
        }),
        ('Stock & logistique', {
            'fields': ('quantite_stock', 'statut', 'poids', 'garantie', 'livraison_disponible')
        }),
        ('Localisation', {
            'fields': ('ville', 'adresse')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    def prix_display(self, obj):
        if obj.is_en_promo:
            return format_html(
                '<span style="text-decoration:line-through;color:#9ca3af;">{} FCFA</span> '
                '<span style="color:#ea580c;font-weight:bold;">{} FCFA</span>',
                obj.prix, obj.prix_actuel
            )
        return format_html('{} FCFA', obj.prix)
    prix_display.short_description = 'Prix'

    def statut_badge(self, obj):
        colors = {
            'disponible': ('#d1fae5', '#065f46'),
            'rupture': ('#fee2e2', '#dc2626'),
            'precommande': ('#fef3c7', '#b45309'),
        }
        bg, fg = colors.get(obj.statut, ('#f3f4f6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:99px;font-size:11px;font-weight:700;">{}</span>',
            bg, fg, obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'
