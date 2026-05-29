from django.contrib import admin
from django.utils.html import format_html
from .models import *


# =====================================================
# CATEGORY
# =====================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "active", "image")
    list_filter = ("active",)
    search_fields = ("name", "image")
    ordering = ("order",)


# =====================================================
# INGREDIENT
# =====================================================
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "price_delta", "time_minutes_delta", "is_allergen", "active")
    list_filter = ("is_allergen", "active")
    search_fields = ("name",)


# =====================================================
# RESTAURANT IMAGE INLINE
# =====================================================
class RestaurantImageInline(admin.TabularInline):
    model = RestaurantImage
    extra = 1
    fields = ("image", "type_image", "titre", "ordre", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" height="80" />', obj.image)
        return "-"
    image_preview.short_description = "Preview"


# =====================================================
# RESTAURANT
# =====================================================
@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("nom", "ville", "type_cuisine", "telephone", "date_creation")
    search_fields = ("nom", "ville", "type_cuisine")
    list_filter = ("ville", "pays")
    inlines = [RestaurantImageInline]

    readonly_fields = ("date_creation", "date_mise_a_jour")

    fieldsets = (
        ("Informations générales", {
            "fields": ("nom", "description", "type_cuisine")
        }),
        ("Adresse", {
            "fields": ("adresse", "ville", "code_postal", "pays", "latitude", "longitude")
        }),
        ("Contact", {
            "fields": ("telephone", "email", "site_web")
        }),
        ("Médias", {
            "fields": ("photo_principale",)
        }),
        ("Dates", {
            "fields": ("date_creation", "date_mise_a_jour")
        }),
    )


# =====================================================
# DISH INGREDIENT INLINE
# =====================================================
class DishIngredientInline(admin.TabularInline):
    model = DishIngredient
    extra = 1
    autocomplete_fields = ("ingredient",)


# =====================================================
# DISH
# =====================================================
@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ("title", "restaurant", "category", "base_price", "active", "image_preview")
    list_filter = ("active", "restaurant", "category")
    search_fields = ("title", "slug")
    autocomplete_fields = ("restaurant", "category")
    inlines = [DishIngredientInline]

    fieldsets = (
        ("Général", {
            "fields": ("restaurant", "title", "slug", "short_description", "description")
        }),
        ("Image", {
            "fields": ("image",)
        }),
        ("Prix & Temps", {
            "fields": ("base_price", "base_time_minutes")
        }),
        ("Relations", {
            "fields": ("category", "ingredients")
        }),
        ("Statut", {
            "fields": ("active",)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" />', obj.image)
        return "-"
    image_preview.short_description = "Image"


# =====================================================
# ADD-ON
# =====================================================
@admin.register(AddOnOption)
class AddOnOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "additional_time_minutes", "active")
    list_filter = ("active",)
    search_fields = ("name",)


# =====================================================
# FULFILLMENT
# =====================================================
@admin.register(FulfillmentOption)
class FulfillmentOptionAdmin(admin.ModelAdmin):
    list_display = ("display_name", "type", "base_fee", "estimated_extra_minutes", "active")
    list_filter = ("type", "active")
    search_fields = ("display_name",)


# =====================================================
# ORDER ITEM INLINE
# =====================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_price", "base_time_minutes")


# =====================================================
# ORDER
# =====================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "phone_number")
    readonly_fields = ("subtotal", "delivery_fee", "total")
    inlines = [OrderItemInline]


# =====================================================
# PAYMENT
# =====================================================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "amount", "captured", "created_at")
    list_filter = ("captured",)
    search_fields = ("provider_payment_id",)