from django.contrib import admin
from django.utils.html import format_html
from .models import Category, WigProduct, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('miniature_preview', 'image', 'couleur', 'tailles', 'principale', 'ordre', 'description')
    readonly_fields = ('miniature_preview',)
    filter_horizontal = ('tailles',)

    def miniature_preview(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" width="60" height="60" style="object-fit:cover;border-radius:6px;"/>', obj.image.url)
        return '—'
    miniature_preview.short_description = 'Aperçu'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'parent')
    search_fields = ('name',)


@admin.register(WigProduct)
class WigProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'shop', 'category', 'prix_display',
        'remise_badge', 'stock', 'status', 'delivery_available', 'created_at'
    )
    list_filter = ('status', 'material', 'texture', 'delivery_available', 'category')
    search_fields = ('name', 'description', 'color', 'shop__name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Infos produit', {
            'fields': ('name', 'shop', 'category', 'description', 'status')
        }),
        ('Caractéristiques', {
            'fields': ('color', 'length', 'texture', 'material', 'stock', 'video')
        }),
        ('Prix', {
            'fields': ('price', 'promotional_price', 'promo_debut', 'promo_fin'),
        }),
        ('Localisation & livraison', {
            'fields': ('city', 'location', 'delivery_available')
        }),
        ('Évaluations', {
            'fields': ('average_rating', 'reviews_count')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [ProductImageInline]

    def prix_display(self, obj):
        if obj.is_en_promo:
            return format_html(
                '<span style="text-decoration:line-through;color:#9ca3af;">{} FCFA</span> '
                '<strong style="color:#dc2626;">{} FCFA</strong>',
                f'{obj.price:,.0f}', f'{obj.promotional_price:,.0f}'
            )
        return f'{obj.price:,.0f} FCFA'
    prix_display.short_description = 'Prix'

    def remise_badge(self, obj):
        if obj.is_en_promo:
            return format_html(
                '<span style="background:#dc2626;color:#fff;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:700;">-{}%</span>',
                obj.remise_pct
            )
        return '—'
    remise_badge.short_description = 'Promo'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('miniature', 'product', 'couleur', 'principale', 'ordre', 'date_ajout')
    list_filter = ('principale', 'couleur')
    filter_horizontal = ('tailles',)
    search_fields = ('product__name', 'description')

    def miniature(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" style="object-fit:cover;border-radius:5px;"/>', obj.image.url)
        return '—'
    miniature.short_description = 'Image'
