from django.contrib import admin
from django.utils.html import format_html
from .models import CarCategory, Car, CarImage, CarAvailability, Reservation


# ── Inlines ───────────────────────────────────────────────────────────────────

class CarImageInline(admin.TabularInline):
    model   = CarImage
    extra   = 2
    fields  = ('miniature', 'image', 'principale', 'ordre', 'description')
    readonly_fields = ('miniature',)

    def miniature(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="70" height="55" style="object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        return "—"
    miniature.short_description = "Aperçu"


class CarAvailabilityInline(admin.TabularInline):
    model  = CarAvailability
    extra  = 1
    fields = ('available_from', 'available_to')


class ReservationInline(admin.TabularInline):
    model          = Reservation
    extra          = 0
    readonly_fields = ('client', 'date_debut', 'date_fin', 'nombre_jours',
                       'prix_total', 'telephone', 'statut', 'created_at')
    fields         = readonly_fields
    can_delete     = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


# ── CarCategory ───────────────────────────────────────────────────────────────

@admin.register(CarCategory)
class CarCategoryAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'nb_vehicules')
    search_fields = ('name',)

    def nb_vehicules(self, obj):
        return obj.cars.count()
    nb_vehicules.short_description = "Véhicules"


# ── Car ───────────────────────────────────────────────────────────────────────

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display  = ('miniature_thumb', 'nom_complet', 'category', 'shop',
                     'prix_display', 'remise_badge', 'statut_badge',
                     'seats', 'transmission', 'city', 'created_at')
    list_filter   = ('status', 'category', 'transmission', 'fuel',
                     'driver_included', 'air_conditioning', 'shop')
    search_fields = ('brand', 'model', 'description', 'city', 'shop__name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Identité du véhicule', {
            'fields': ('shop', 'category', 'brand', 'model', 'year', 'color', 'status')
        }),
        ('Caractéristiques techniques', {
            'fields': (
                ('seats', 'doors'),
                ('transmission', 'fuel'),
                ('air_conditioning', 'driver_included'),
                'luggage_capacity',
            )
        }),
        ('Prix & Promotion', {
            'fields': (
                'daily_price',
                ('promotional_price', 'promo_debut', 'promo_fin'),
                'deposit',
            )
        }),
        ('Localisation', {
            'fields': ('city', 'location', 'address')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Dates système', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )

    inlines = [CarImageInline, CarAvailabilityInline, ReservationInline]

    def miniature_thumb(self, obj):
        img = obj.images.filter(principale=True).first() or obj.images.first()
        if img:
            return format_html(
                '<img src="{}" width="55" height="42" style="object-fit:cover;border-radius:5px;" />',
                img.image.url
            )
        return "—"
    miniature_thumb.short_description = "Photo"

    def nom_complet(self, obj):
        return str(obj)
    nom_complet.short_description = "Véhicule"

    def prix_display(self, obj):
        if obj.is_en_promo:
            return format_html(
                '<span style="text-decoration:line-through;color:#9ca3af;">{} FCFA</span> '
                '<strong style="color:#dc2626;">{} FCFA</strong>',
                f'{obj.daily_price:,.0f}', f'{obj.promotional_price:,.0f}'
            )
        return f'{obj.daily_price:,.0f} FCFA / jour'
    prix_display.short_description = "Prix / jour"

    def remise_badge(self, obj):
        if obj.is_en_promo:
            return format_html(
                '<span style="background:#dc2626;color:#fff;padding:2px 8px;'
                'border-radius:99px;font-size:11px;font-weight:700;">-{}%</span>',
                obj.remise_pct
            )
        return '—'
    remise_badge.short_description = "Promo"

    def statut_badge(self, obj):
        colors = {
            'available':   ('#059669', '#d1fae5'),
            'rented':      ('#d97706', '#fef3c7'),
            'maintenance': ('#6b7280', '#f3f4f6'),
        }
        fg, bg = colors.get(obj.status, ('#6b7280', '#f3f4f6'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;border-radius:99px;font-size:11px;font-weight:700;">{}</span>',
            bg, fg, obj.get_status_display()
        )
    statut_badge.short_description = "Statut"


# ── CarImage ──────────────────────────────────────────────────────────────────

@admin.register(CarImage)
class CarImageAdmin(admin.ModelAdmin):
    list_display  = ('miniature', 'car', 'principale', 'ordre', 'date_ajout')
    list_filter   = ('principale',)
    search_fields = ('car__brand', 'car__model')

    def miniature(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="70" height="55" style="object-fit:cover;border-radius:5px;" />',
                obj.image.url
            )
        return "—"
    miniature.short_description = "Photo"


# ── Reservation ───────────────────────────────────────────────────────────────

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display  = ('id', 'car', 'client_nom', 'date_debut', 'date_fin',
                     'nombre_jours', 'prix_total_fmt', 'statut_badge', 'telephone', 'created_at')
    list_filter   = ('statut', 'car__shop', 'date_debut')
    search_fields = ('car__brand', 'car__model', 'client__username', 'client__first_name',
                     'client__last_name', 'telephone')
    readonly_fields = ('nombre_jours', 'prix_total', 'created_at', 'updated_at')
    date_hierarchy  = 'date_debut'

    fieldsets = (
        ('Réservation', {
            'fields': ('car', 'client', 'statut')
        }),
        ('Dates & Prix', {
            'fields': ('date_debut', 'date_fin', 'nombre_jours', 'prix_total')
        }),
        ('Contact client', {
            'fields': ('telephone', 'message_client')
        }),
        ('Dates système', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )

    def client_nom(self, obj):
        return obj.client.get_full_name() or obj.client.username
    client_nom.short_description = "Client"

    def prix_total_fmt(self, obj):
        return f'{obj.prix_total:,.0f} FCFA'
    prix_total_fmt.short_description = "Total"

    def statut_badge(self, obj):
        colors = {
            'pending':   ('#d97706', '#fef3c7'),
            'confirmed': ('#059669', '#d1fae5'),
            'cancelled': ('#dc2626', '#fee2e2'),
            'completed': ('#2563eb', '#dbeafe'),
        }
        fg, bg = colors.get(obj.statut, ('#6b7280', '#f3f4f6'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;border-radius:99px;font-size:11px;font-weight:700;">{}</span>',
            bg, fg, obj.get_statut_display()
        )
    statut_badge.short_description = "Statut"
