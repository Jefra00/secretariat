from django.contrib import admin

from .models import (
    Category,
    Ingredient,
    Restaurant,
    RestaurantImage,
    TypeCuisine,
    Dish,
    DishIngredient,
    AddOnOption,
    FulfillmentOption,
    Order,
    OrderItem,
    OrderItemIngredientChoice,
    DishRating,
    LivreurProfile,
    Payment,
)

@admin.register(TypeCuisine)
class TypeCuisineAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ordre')
    ordering = ('ordre', 'nom')


# -------------------------
# Category
# -------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "active")
    list_filter = ("active",)
    search_fields = ("name",)
    ordering = ("order",)


# -------------------------
# Ingredient
# -------------------------
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price_delta",
        "time_minutes_delta",
        "is_allergen",
        "active",
    )
    list_filter = ("active", "is_allergen")
    search_fields = ("name",)


# -------------------------
# Restaurant Images Inline
# -------------------------
class RestaurantImageInline(admin.TabularInline):
    model = RestaurantImage
    extra = 1


# -------------------------
# Restaurant
# -------------------------
@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("nom", "ville", "est_ouvert", "email")
    list_filter = ("est_ouvert", "ville", "pays")
    list_editable = ("est_ouvert",)
    search_fields = ("nom", "ville", "adresse")
    filter_horizontal = ("types_cuisine",)
    inlines = [RestaurantImageInline]

    @admin.action(description="Marquer comme ouvert")
    def ouvrir_restaurants(self, request, queryset):
        queryset.update(est_ouvert=True)

    @admin.action(description="Marquer comme fermé")
    def fermer_restaurants(self, request, queryset):
        queryset.update(est_ouvert=False)

    actions = ["ouvrir_restaurants", "fermer_restaurants"]


# -------------------------
# DishIngredient Inline
# -------------------------
class DishIngredientInline(admin.TabularInline):
    model = DishIngredient
    extra = 1


# -------------------------
# Dish
# -------------------------
@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "restaurant",
        "category",
        "base_price",
        "active",
    )
    list_filter = (
        "active",
        "category",
        "restaurant",
    )
    search_fields = (
        "title",
        "slug",
    )
    prepopulated_fields = {
        "slug": ("title",)
    }
    filter_horizontal = ("ingredients",)
    inlines = [DishIngredientInline]


# -------------------------
# RestaurantImage
# -------------------------
@admin.register(RestaurantImage)
class RestaurantImageAdmin(admin.ModelAdmin):
    list_display = (
        "restaurant",
        "type_image",
        "titre",
        "ordre",
    )
    list_filter = ("type_image",)
    search_fields = ("restaurant__nom", "titre")


# -------------------------
# DishIngredient
# -------------------------
@admin.register(DishIngredient)
class DishIngredientAdmin(admin.ModelAdmin):
    list_display = (
        "dish",
        "ingredient",
        "default_included",
        "order",
    )
    list_filter = ("default_included",)
    search_fields = (
        "dish__title",
        "ingredient__name",
    )


# -------------------------
# AddOnOption
# -------------------------
@admin.register(AddOnOption)
class AddOnOptionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "additional_time_minutes",
        "active",
    )
    list_filter = ("active",)
    search_fields = ("name",)


# -------------------------
# FulfillmentOption
# -------------------------
@admin.register(FulfillmentOption)
class FulfillmentOptionAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "type",
        "base_fee",
        "estimated_extra_minutes",
        "active",
    )
    list_filter = ("type", "active")


# -------------------------
# OrderItemIngredientChoice Inline
# -------------------------
class OrderItemIngredientChoiceInline(admin.TabularInline):
    model = OrderItemIngredientChoice
    extra = 0


# -------------------------
# OrderItem Inline
# -------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


# -------------------------
# Order
# -------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "total",
        "created_at",
        "livreur",
    )
    list_filter = (
        "status",
        "created_at",
    )
    search_fields = (
        "id",
        "user__username",
        "phone_number",
    )
    readonly_fields = (
        "qr_code",
        "created_at",
    )
    inlines = [OrderItemInline]


# -------------------------
# OrderItem
# -------------------------
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "dish",
        "quantity",
        "line_price",
    )
    autocomplete_fields = ("order", "dish")
    filter_horizontal = ("added_addons",)
    inlines = [OrderItemIngredientChoiceInline]


# -------------------------
# OrderItemIngredientChoice
# -------------------------
@admin.register(OrderItemIngredientChoice)
class OrderItemIngredientChoiceAdmin(admin.ModelAdmin):
    list_display = (
        "order_item",
        "ingredient",
        "choice_type",
    )
    list_filter = ("choice_type",)


# -------------------------
# DishRating
# -------------------------
@admin.register(DishRating)
class DishRatingAdmin(admin.ModelAdmin):
    list_display = (
        "dish",
        "user",
        "rating",
        "created_at",
    )
    list_filter = ("rating",)
    search_fields = (
        "dish__title",
        "user__username",
    )


# -------------------------
# LivreurProfile
# -------------------------
@admin.register(LivreurProfile)
class LivreurProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "matricule_moto",
        "disponible",
        "zone_radius",
    )
    list_filter = ("disponible",)
    search_fields = (
        "user__username",
        "matricule_moto",
    )


# -------------------------
# Payment
# -------------------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "provider",
        "amount",
        "captured",
        "created_at",
    )
    list_filter = ("captured", "provider")
    search_fields = (
        "provider_payment_id",
        "order__id",
    )