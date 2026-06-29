from django.conf import settings
from django.contrib.gis.db import models
from django.utils import timezone
from decimal import Decimal
import uuid


# ---------------------------
# Constants / helpers
# ---------------------------
CURRENCY_DECIMAL_PLACES = 2
CURRENCY_MAX_DIGITS = 10


# ---------------------------
# Utilisateur (optionnel)
# ---------------------------
User = settings.AUTH_USER_MODEL


# ---------------------------
# Catégorie
# ---------------------------
class Category(models.Model):
    """
    Catégorie simple avec ordre d'affichage.
    """
    name = models.CharField(max_length=140)
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    image = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


# ---------------------------
# Ingrédient
# ---------------------------
class Ingredient(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price_delta = models.DecimalField(
        max_digits=CURRENCY_MAX_DIGITS,
        decimal_places=CURRENCY_DECIMAL_PLACES,
        default=Decimal('0.00')
    )
    time_minutes_delta = models.IntegerField(default=0)
    is_allergen = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    

    def __str__(self):
        return self.name


class TypeCuisine(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = 'Type de cuisine'
        verbose_name_plural = 'Types de cuisine'

    def __str__(self):
        return self.nom


class Restaurant(models.Model):

    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    # Vendeur/propriétaire du restaurant
    proprietaire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='restaurants',
        verbose_name='Propriétaire',
    )

    type_cuisine = models.CharField(max_length=100, blank=True)
    types_cuisine = models.ManyToManyField(
        'TypeCuisine',
        blank=True,
        related_name='restaurants',
        verbose_name='Types de cuisine',
    )
    

    adresse = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=20)
    pays = models.CharField(max_length=100)

    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    location = models.PointField(geography=True, null=True, blank=True)

    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.URLField(blank=True)

    # ✅ Photo principale
    photo_principale = models.CharField(max_length=500, blank=True, null=True)

    est_ouvert = models.BooleanField(default=True, verbose_name='Ouvert')

    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.latitude and self.longitude:
            from django.contrib.gis.geos import Point
            self.location = Point(float(self.longitude), float(self.latitude), srid=4326)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom

    def google_maps_url(self):
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps/dir/?api=1&destination={self.latitude},{self.longitude}"
        return None

class RestaurantImage(models.Model):

    TYPE_CHOICES = [
        ('banner', 'Bannière'),
        ('gallery', 'Galerie'),
        ('menu', 'Menu'),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.CharField(max_length=500, blank=True, null=True)
    type_image = models.CharField(max_length=20, choices=TYPE_CHOICES, default='gallery')
    titre = models.CharField(max_length=150, blank=True)
    ordre = models.PositiveIntegerField(default=0)

    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return f"{self.restaurant.nom} - {self.type_image}"
# ---------------------------
# Plat (Dish)
# ---------------------------
class Dish(models.Model):

    # 🔹 Relation avec Restaurant
    restaurant = models.ForeignKey(
        "Restaurant",
        on_delete=models.CASCADE,
        related_name="dishes",
        blank=True, null=True
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # ✅ On stocke l’URL, pas un fichier
    image = models.CharField(max_length=500, blank=True, null=True)

    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    base_time_minutes = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dishes"
    )
    
    ingredients = models.ManyToManyField("Ingredient", blank=True)

    def __str__(self):
        return self.title


    # ------------------------------------------------
    # Calcul dynamique prix + temps
    # ------------------------------------------------
    def calculate_price_and_time(
        self,
        included_ingredient_ids=None,
        added_ingredient_ids=None,
        removed_ingredient_ids=None
    ):
        if included_ingredient_ids is None:
            included_ingredient_ids = []
        if added_ingredient_ids is None:
            added_ingredient_ids = []
        if removed_ingredient_ids is None:
            removed_ingredient_ids = []

        price = Decimal(self.base_price)
        time_minutes = int(self.base_time_minutes)

        dish_ings = DishIngredient.objects.filter(dish=self).select_related('ingredient')

        default_included = {di.ingredient.id: di for di in dish_ings if di.default_included}

        # Ingrédients par défaut
        for ing_id, di in default_included.items():
            ing = di.ingredient
            if ing_id in removed_ingredient_ids:
                price -= Decimal(di.price_override if di.price_override is not None else ing.price_delta)
                time_minutes -= int(di.time_minutes_override if di.time_minutes_override is not None else ing.time_minutes_delta)
            else:
                price += Decimal(di.price_override if di.price_override is not None else ing.price_delta)
                time_minutes += int(di.time_minutes_override if di.time_minutes_override is not None else ing.time_minutes_delta)

        # Ajouts explicites
        all_candidate_added_ids = set(added_ingredient_ids) | set(included_ingredient_ids)
        for ing_id in all_candidate_added_ids:
            if ing_id in default_included and ing_id not in removed_ingredient_ids:
                continue
            try:
                di = DishIngredient.objects.get(dish=self, ingredient_id=ing_id)
                ing = di.ingredient
                price += Decimal(di.price_override if di.price_override is not None else ing.price_delta)
                time_minutes += int(di.time_minutes_override if di.time_minutes_override is not None else ing.time_minutes_delta)
            except DishIngredient.DoesNotExist:
                try:
                    ing = Ingredient.objects.get(pk=ing_id)
                    price += Decimal(ing.price_delta)
                    time_minutes += int(ing.time_minutes_delta)
                except Ingredient.DoesNotExist:
                    continue

        if price < Decimal('0.00'):
            price = Decimal('0.00')
        if time_minutes < 0:
            time_minutes = 0

        return price.quantize(Decimal('1.00')), time_minutes


# ---------------------------
# Liaison Plat <-> Ingrédient
# ---------------------------
class DishIngredient(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='dish_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='ingredient_dishes')
    default_included = models.BooleanField(default=False)

    price_override = models.DecimalField(
        max_digits=CURRENCY_MAX_DIGITS,
        decimal_places=CURRENCY_DECIMAL_PLACES,
        null=True,
        blank=True
    )
    time_minutes_override = models.IntegerField(null=True, blank=True)

    quantity = models.CharField(max_length=50, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('dish', 'ingredient')
        ordering = ['order']

    def __str__(self):
        return f"{self.ingredient.name} in {self.dish.title}"


# ---------------------------
# Add-on
# ---------------------------
class AddOnOption(models.Model):
    name = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES)
    additional_time_minutes = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (+{self.price})"


# ---------------------------
# Delivery / Pickup
# ---------------------------
class FulfillmentOption(models.Model):
    DELIVERY = 'delivery'
    PICKUP = 'pickup'
    FULFILLMENT_CHOICES = [
        (DELIVERY, 'Delivery'),
        (PICKUP, 'Pickup'),
    ]

    type = models.CharField(max_length=20, choices=FULFILLMENT_CHOICES)
    display_name = models.CharField(max_length=120)
    base_fee = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=Decimal('0.00'))
    estimated_extra_minutes = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.display_name} ({self.type})"


# ---------------------------
# Commande
# ---------------------------
class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_DONE = 'done'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_IN_PROGRESS, 'In progress'),
        (STATUS_DONE, 'Done'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resto_orders'  # IMPORTANT : évite les conflits
    )

    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    fulfillment = models.ForeignKey(FulfillmentOption, on_delete=models.SET_NULL, null=True, blank=True)

    delivery_address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    delivery_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    delivery_lng = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)


    subtotal = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=Decimal('0.00'))
    delivery_fee = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=Decimal('0.00'))
    estimated_ready_at = models.DateTimeField(null=True, blank=True)

    qr_code = models.CharField(max_length=255, unique=True, blank=True)
    qr_validated = models.BooleanField(default=False)
    qr_validated_at = models.DateTimeField(null=True, blank=True)

    livreur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='livraisons'
    )
    livreur_reserved_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['livreur', 'status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.status}"

    def recalc_totals(self):
        items = self.items.all()
        subtotal = sum([Decimal(item.line_price) for item in items])
        self.subtotal = subtotal.quantize(Decimal('1.00'))
        self.delivery_fee = self.fulfillment.base_fee if self.fulfillment else Decimal('0.00')
        self.total = (self.subtotal + self.delivery_fee).quantize(Decimal('1.00'))
        self.save(update_fields=['subtotal', 'delivery_fee', 'total'])
    
    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.qr_code = str(uuid.uuid4())
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Dish, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    line_price = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=Decimal('0.00'))
    base_time_minutes = models.IntegerField(default=0)

    added_addons = models.ManyToManyField(AddOnOption, blank=True, related_name='order_items')

    def __str__(self):
        return f"{self.quantity}x {self.dish.title}"

    def recalc_line(self):
        choices = self.ingredient_choices.all()
        added_ids = [c.ingredient_id for c in choices if c.choice_type == OrderItemIngredientChoice.CHOICE_ADD]
        removed_ids = [c.ingredient_id for c in choices if c.choice_type == OrderItemIngredientChoice.CHOICE_REMOVE]

        price_per_unit, time_per_unit = self.dish.calculate_price_and_time(
            added_ingredient_ids=added_ids,
            removed_ingredient_ids=removed_ids
        )

        addons_total = sum([a.price for a in self.added_addons.all()])
        final_price_per_unit = price_per_unit + Decimal(addons_total)

        self.line_price = (final_price_per_unit * self.quantity).quantize(Decimal('1.00'))
        self.base_time_minutes = time_per_unit
        self.save(update_fields=['line_price', 'base_time_minutes'])


class OrderItemIngredientChoice(models.Model):
    CHOICE_ADD = 'add'
    CHOICE_REMOVE = 'remove'
    CHOICE_KEEP = 'keep'

    CHOICE_TYPES = [
        (CHOICE_ADD, 'Add'),
        (CHOICE_REMOVE, 'Remove'),
        (CHOICE_KEEP, 'Keep'),
    ]

    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='ingredient_choices')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    choice_type = models.CharField(max_length=10, choices=CHOICE_TYPES, default=CHOICE_KEEP)

    class Meta:
        unique_together = ('order_item', 'ingredient')

    def __str__(self):
        return f"{self.choice_type} {self.ingredient.name}"


# ---------------------------
# Notation plat
# ---------------------------
class DishRating(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dish_ratings'
    )
    rating = models.PositiveSmallIntegerField()  # 1 à 5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('dish', 'user')

    def __str__(self):
        return f"{self.user} → {self.dish.title} : {self.rating}★"


# ---------------------------
# Profil Livreur
# ---------------------------
class LivreurProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='livreur_profile'
    )
    matricule_moto = models.CharField(max_length=50)
    photo_url = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    location = models.PointField(geography=True, null=True, blank=True)
    location_updated_at = models.DateTimeField(null=True, blank=True)
    zone_radius = models.IntegerField(default=8000)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"Livreur {self.user.get_full_name()} — {self.matricule_moto}"


# ---------------------------
# Paiement
# ---------------------------
class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    provider = models.CharField(max_length=60, blank=True)
    provider_payment_id = models.CharField(max_length=180, blank=True)
    amount = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES)
    captured = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id}"
