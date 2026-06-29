from django.contrib import admin
from django.utils.html import format_html
from .models import ImmobilierCategory, Immobilier, PhotoImmobilier, VideoImmobilier, DemandeVisite


# ── Inlines ───────────────────────────────────────────────────────────────────

class PhotoInline(admin.TabularInline):
    model   = PhotoImmobilier
    extra   = 3
    fields  = ('apercu', 'image', 'principale', 'ordre')
    readonly_fields = ('apercu',)

    def apercu(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="80" height="60" style="object-fit:cover;border-radius:6px;" />',
                obj.image.url,
            )
        return "—"
    apercu.short_description = "Aperçu"


class DemandeVisiteInline(admin.TabularInline):
    model           = DemandeVisite
    extra           = 0
    readonly_fields = ('client', 'date_souhaitee', 'heure_souhaitee', 'telephone', 'statut', 'created_at')
    fields          = readonly_fields
    can_delete      = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


# ── ImmobilierCategory ────────────────────────────────────────────────────────

@admin.register(ImmobilierCategory)
class ImmobilierCategoryAdmin(admin.ModelAdmin):
    list_display  = ('icon', 'nom', 'nb_biens')
    search_fields = ('nom',)

    def nb_biens(self, obj):
        return obj.biens.count()
    nb_biens.short_description = "Biens"


# ── Immobilier ────────────────────────────────────────────────────────────────

@admin.register(Immobilier)
class ImmobilierAdmin(admin.ModelAdmin):
    list_display  = ('photo_thumb', 'titre', 'type_badge', 'offre_badge', 'vendeur',
                     'prix_display', 'promo_badge', 'statut_badge', 'ville', 'date_creation')
    list_filter   = ('statut', 'type_bien', 'type_offre', 'categorie', 'vendeur',
                     'meuble', 'piscine', 'parking', 'gardien')
    search_fields = ('titre', 'description', 'vendeur__nom')
    readonly_fields = ('date_creation', 'date_modification')

    fieldsets = (
        ('Identité du bien', {
            'fields': ('vendeur', 'categorie', 'titre', 'type_bien', 'type_offre', 'statut'),
        }),
        ('Prix & Caution', {
            'fields': (
                'prix',
                ('prix_promotionnel', 'promo_debut', 'promo_fin'),
                'caution',
            ),
        }),
        ('Caractéristiques', {
            'fields': (
                'superficie',
                ('nombre_chambres', 'nombre_salles_bain'),
                ('nombre_salons', 'nombre_cuisines', 'nombre_garages'),
                ('etage', 'annee_construction'),
                'meuble',
            ),
        }),
        ('Équipements', {
            'fields': (
                ('piscine', 'parking', 'gardien'),
                ('wifi', 'climatisation', 'generatrice', 'eau_courante'),
            ),
        }),
        ('Localisation', {
            'fields': ('ville', 'quartier'),
        }),
        ('Description', {
            'fields': ('description',),
        }),
        ('Dates système', {
            'classes': ('collapse',),
            'fields': ('date_creation', 'date_modification'),
        }),
    )

    inlines = [PhotoInline, DemandeVisiteInline]

    def photo_thumb(self, obj):
        photo = obj.photos.filter(principale=True).first() or obj.photos.first()
        if photo:
            return format_html(
                '<img src="{}" width="60" height="45" style="object-fit:cover;border-radius:5px;" />',
                photo.image.url,
            )
        return "—"
    photo_thumb.short_description = "Photo"

    def type_badge(self, obj):
        colors = {
            'maison':      '#7c3aed', 'villa':      '#0891b2',
            'appartement': '#2563eb', 'studio':     '#059669',
            'terrain':     '#d97706', 'bureau':     '#6b7280',
            'commerce':    '#dc2626', 'entrepot':   '#9ca3af',
        }
        color = colors.get(obj.type_bien, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:700;">{}</span>',
            color, obj.get_type_bien_display(),
        )
    type_badge.short_description = "Type"

    def offre_badge(self, obj):
        c = '#0891b2' if obj.type_offre == 'location' else '#059669'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:700;">{}</span>',
            c, obj.get_type_offre_display(),
        )
    offre_badge.short_description = "Offre"

    def prix_display(self, obj):
        if obj.is_en_promo:
            return format_html(
                '<span style="text-decoration:line-through;color:#9ca3af;">{} FCFA</span> '
                '<strong style="color:#dc2626;">{} FCFA</strong>',
                f'{obj.prix:,.0f}', f'{obj.prix_promotionnel:,.0f}',
            )
        return f'{obj.prix:,.0f} FCFA{obj.suffix_prix}'
    prix_display.short_description = "Prix"

    def promo_badge(self, obj):
        if obj.is_en_promo:
            return format_html(
                '<span style="background:#dc2626;color:#fff;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:700;">-{}%</span>',
                obj.remise_pct,
            )
        return '—'
    promo_badge.short_description = "Promo"

    def statut_badge(self, obj):
        colors = {
            'disponible': ('#059669', '#d1fae5'),
            'reserve':    ('#d97706', '#fef3c7'),
            'vendu':      ('#6b7280', '#f3f4f6'),
            'loue':       ('#2563eb', '#dbeafe'),
        }
        fg, bg = colors.get(obj.statut, ('#6b7280', '#f3f4f6'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;border-radius:99px;font-size:11px;font-weight:700;">{}</span>',
            bg, fg, obj.get_statut_display(),
        )
    statut_badge.short_description = "Statut"


# ── PhotoImmobilier ───────────────────────────────────────────────────────────

@admin.register(PhotoImmobilier)
class PhotoImmobilierAdmin(admin.ModelAdmin):
    list_display  = ('apercu', 'bien', 'principale', 'ordre', 'date_creation')
    list_filter   = ('principale',)
    search_fields = ('bien__titre',)

    def apercu(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="70" height="52" style="object-fit:cover;border-radius:5px;" />',
                obj.image.url,
            )
        return "—"
    apercu.short_description = "Photo"


# ── DemandeVisite ─────────────────────────────────────────────────────────────

@admin.register(DemandeVisite)
class DemandeVisiteAdmin(admin.ModelAdmin):
    list_display  = ('id', 'bien', 'client_nom', 'date_souhaitee', 'heure_souhaitee',
                     'telephone', 'statut_badge', 'created_at')
    list_filter   = ('statut', 'bien__vendeur', 'date_souhaitee')
    search_fields = ('bien__titre', 'client__username', 'client__first_name',
                     'client__last_name', 'telephone')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy  = 'date_souhaitee'

    fieldsets = (
        ('Demande', {
            'fields': ('bien', 'client', 'statut'),
        }),
        ('Rendez-vous', {
            'fields': ('date_souhaitee', 'heure_souhaitee'),
        }),
        ('Contact', {
            'fields': ('telephone', 'message'),
        }),
        ('Dates système', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def client_nom(self, obj):
        return obj.client.get_full_name() or obj.client.username
    client_nom.short_description = "Client"

    def statut_badge(self, obj):
        colors = {
            'pending':   ('#d97706', '#fef3c7'),
            'confirmed': ('#059669', '#d1fae5'),
            'cancelled': ('#dc2626', '#fee2e2'),
            'done':      ('#2563eb', '#dbeafe'),
        }
        fg, bg = colors.get(obj.statut, ('#6b7280', '#f3f4f6'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;border-radius:99px;font-size:11px;font-weight:700;">{}</span>',
            bg, fg, obj.get_statut_display(),
        )
    statut_badge.short_description = "Statut"
