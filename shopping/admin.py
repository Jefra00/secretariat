from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Category,
    Vendor,
    Shop,
    Product,
    Taille,
    Couleur,
    ProductImage
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'parent'
    )
    search_fields = (
        'name',
    )


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        'business_name',
        'user',
        'verified',
        'created_at'
    )
    list_filter = (
        'verified',
        'created_at'
    )
    search_fields = (
        'business_name',
        'user__username',
        'user__email'
    )
    readonly_fields = (
        'created_at',
    )


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'vendor',
        'ville',
        'commune',
        'quartier',
        'active',
        'created_at'
    )
    list_filter = (
        'active',
        'ville',
        'commune'
    )
    search_fields = (
        'name',
        'address',
        'vendor__business_name'
    )
    prepopulated_fields = {
        'slug': ('name',)
    }
    readonly_fields = (
        'created_at',
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'shop', 'category', 'prix_display',
        'remise_badge', 'stock', 'active', 'created_at'
    )

    list_filter = ('active', 'category', 'shop')

    search_fields = ('name', 'description', 'shop__name')

    prepopulated_fields = {'slug': ('name',)}

    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Infos', {'fields': ('name', 'slug', 'shop', 'category', 'description', 'stock', 'active')}),
        ('Prix', {'fields': ('price', 'prix_promo', 'promo_debut', 'promo_fin')}),
        ('Dates', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    inlines = [ProductImageInline]

    def prix_display(self, obj):
        if obj.is_en_promo:
            return format_html(
                '<span style="text-decoration:line-through;color:#9ca3af;">{} FCFA</span> '
                '<strong style="color:#dc2626;">{} FCFA</strong>',
                f'{obj.price:,.0f}', f'{obj.prix_promo:,.0f}'
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


@admin.register(Taille)
class TailleAdmin(admin.ModelAdmin):
    list_display = (
        'nom',
        'description'
    )

    search_fields = (
        'nom',
    )


@admin.register(Couleur)
class CouleurAdmin(admin.ModelAdmin):
    list_display = (
        'nom',
        'apercu_couleur',
        'code_hex'
    )

    search_fields = (
        'nom',
    )

    def apercu_couleur(self, obj):
        if obj.code_hex:
            return format_html(
                '<div style="width:30px;height:30px;background:{};border:1px solid #000;"></div>',
                obj.code_hex
            )
        return "-"

    apercu_couleur.short_description = "Couleur"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):

    list_display = (
        'miniature',
        'product',
        'couleur',
        'principale',
        'ordre',
        'date_ajout'
    )

    list_filter = (
        'principale',
        'couleur'
    )

    filter_horizontal = (
        'tailles',
    )

    search_fields = (
        'product__name',
        'description'
    )

    def miniature(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="60" height="60" style="object-fit:cover;border-radius:5px;" />',
                obj.image.url
            )
        return "-"

    miniature.short_description = "Image"