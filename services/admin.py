from django.contrib import admin
from django.utils.html import format_html
from .models import ServiceCategory, Service,ServiceImage, ServiceTexte


# ============ CATÉGORIE DE SERVICES ============
@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('display_image_admin', 'nom', 'ordre_affichage', 'actif', 'date_creation')
    list_display_links = ('nom',)
    list_editable = ('ordre_affichage', 'actif')
    search_fields = ('nom', 'description')
    list_filter = ('actif',)
    ordering = ('ordre_affichage',)

    # Champs non modifiables dans l’admin
    readonly_fields = ('slug', 'preview_image', 'date_creation', 'date_modification')

    fieldsets = (
        ('Informations principales', {
            'fields': ('nom', 'description', 'slug')
        }),
        ('Affichage', {
            'fields': ('image', 'icon_name', 'preview_image', 'ordre_affichage', 'actif')
        }),
        ('Dates (lecture seule)', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    def display_image_admin(self, obj):
        """Affiche une miniature ou une icône dans la liste admin"""
        if obj.image:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius:6px;object-fit:cover;" />',
                obj.image.url
            )
        elif obj.icon_name:
            return format_html(
                '<span class="material-symbols-outlined" style="font-size:28px;">{}</span>',
                obj.icon_name
            )
        return format_html('<span style="color:#999;">–</span>')
    display_image_admin.short_description = "Aperçu"

    def preview_image(self, obj):
        """Aperçu visuel dans le formulaire admin"""
        if obj.image:
            return format_html(
                '<img src="{}" width="100" style="border-radius:8px;object-fit:cover;margin:8px 0;" />',
                obj.image.url
            )
        elif obj.icon_name:
            return format_html(
                '<span class="material-symbols-outlined" style="font-size:48px;">{}</span>',
                obj.icon_name
            )
        return "Aucune image ou icône"
    preview_image.short_description = "Aperçu visuel"

    class Media:
        css = {
            'all': ('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined',)
        }


# ============ SERVICES ============
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('display_image_admin', 'nom', 'category', 'prix_base', 'remise', 'populaire', 'actif')
    list_display_links = ('nom',)
    list_editable = ('actif', 'populaire')
    search_fields = ('nom', 'description', 'category__nom')
    list_filter = ('actif', 'populaire', 'category')
    ordering = ('nom',)

    # Champs non modifiables dans l’admin
    readonly_fields = ('slug', 'preview_image', 'date_creation', 'date_modification')

    fieldsets = (
        ('Informations principales', {
            'fields': ('category', 'nom', 'slug', 'description', 'avantages')
        }),
        ('Tarification & délais', {
            'fields': ('prix_base', 'remise', 'delai_moyen')
        }),
        ('Affichage', {
            'fields': ('image', 'icon_name', 'preview_image', 'populaire', 'actif')
        }),
        ('Dates (lecture seule)', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    def display_image_admin(self, obj):
        """Aperçu miniature dans la liste"""
        if obj.image:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius:6px;object-fit:cover;" />',
                obj.image.url
            )
        elif obj.icon_name:
            return format_html(
                '<span class="material-symbols-outlined" style="font-size:26px;">{}</span>',
                obj.icon_name
            )
        return format_html('<span style="color:#999;">–</span>')
    display_image_admin.short_description = "Aperçu"

    def preview_image(self, obj):
        """Aperçu visuel dans le formulaire"""
        if obj.image:
            return format_html(
                '<img src="{}" width="100" style="border-radius:8px;object-fit:cover;margin:8px 0;" />',
                obj.image.url
            )
        elif obj.icon_name:
            return format_html(
                '<span class="material-symbols-outlined" style="font-size:48px;">{}</span>',
                obj.icon_name
            )
        return "Aucune image ou icône"
    preview_image.short_description = "Aperçu visuel"

    class Media:
        css = {
            'all': ('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined',)
        }


# ============ INLINES ============
class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ('image', 'titre', 'ordre', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image.url}" width="60" style="border-radius:6px;object-fit:cover;">')
        return "–"
    preview.short_description = "Aperçu"


class ServiceTexteInline(admin.TabularInline):
    model = ServiceTexte
    extra = 1
    fields = ('titre', 'contenu', 'ordre')


admin.site.register(ServiceImage)
admin.site.register(ServiceTexte)