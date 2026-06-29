from django.db import models
from django.conf import settings


class CarCategory(models.Model):
    name  = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    icon  = models.CharField(max_length=50,  blank=True, verbose_name="Icône emoji")

    class Meta:
        verbose_name          = "Catégorie de véhicule"
        verbose_name_plural   = "Catégories de véhicules"
        ordering              = ['name']

    def __str__(self):
        return f"{self.icon} {self.name}".strip()


class Car(models.Model):

    TRANSMISSION_CHOICES = (
        ("manual",    "Manuelle"),
        ("automatic", "Automatique"),
    )
    FUEL_CHOICES = (
        ("gasoline", "Essence"),
        ("diesel",   "Diesel"),
        ("hybrid",   "Hybride"),
        ("electric", "Électrique"),
    )
    STATUS_CHOICES = (
        ("available",   "Disponible"),
        ("rented",      "Louée"),
        ("maintenance", "En maintenance"),
    )

    # ── Propriétaire ──────────────────────────────────────────────────────────
    shop = models.ForeignKey(
        'boutique.Boutique',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="voiture",
        verbose_name="Agence / Propriétaire"
    )
    category = models.ForeignKey(
        CarCategory,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="cars",
        verbose_name="Catégorie"
    )

    # ── Identité véhicule ─────────────────────────────────────────────────────
    brand = models.CharField(max_length=100, verbose_name="Marque")
    model = models.CharField(max_length=100, verbose_name="Modèle")
    year  = models.PositiveIntegerField(verbose_name="Année")
    color = models.CharField(max_length=80, blank=True, verbose_name="Couleur")

    # ── Caractéristiques techniques ───────────────────────────────────────────
    seats             = models.PositiveIntegerField(verbose_name="Nombre de places")
    doors             = models.PositiveIntegerField(default=4, verbose_name="Nombre de portes")
    transmission      = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, verbose_name="Transmission")
    fuel              = models.CharField(max_length=20, choices=FUEL_CHOICES, verbose_name="Carburant")
    air_conditioning  = models.BooleanField(default=True, verbose_name="Climatisation")
    luggage_capacity  = models.PositiveIntegerField(default=0, verbose_name="Capacité bagages (valises)")
    driver_included   = models.BooleanField(default=False, verbose_name="Chauffeur inclus")

    # ── Prix & promotion ──────────────────────────────────────────────────────
    daily_price        = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix / jour (FCFA)")
    promotional_price  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix promo / jour (FCFA)")
    promo_debut        = models.DateField(null=True, blank=True, verbose_name="Début promotion")
    promo_fin          = models.DateField(null=True, blank=True, verbose_name="Fin promotion")
    deposit            = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Caution (FCFA)")

    # ── Localisation ──────────────────────────────────────────────────────────
    city     = models.CharField(max_length=150, blank=True, verbose_name="Ville")
    location = models.CharField(max_length=255, blank=True, verbose_name="Lieu de prise en charge")
    address  = models.CharField(max_length=255, blank=True, verbose_name="Adresse complète")

    # ── Contenu éditorial ─────────────────────────────────────────────────────
    description = models.TextField(verbose_name="Description")

    # ── Statut ────────────────────────────────────────────────────────────────
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available", verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"

    # ── Propriétés promo ──────────────────────────────────────────────────────
    @property
    def is_en_promo(self):
        from datetime import date
        if not self.promotional_price or self.promotional_price >= self.daily_price:
            return False
        today = date.today()
        if self.promo_debut and self.promo_debut > today:
            return False
        if self.promo_fin and self.promo_fin < today:
            return False
        return True

    @property
    def prix_actuel(self):
        return self.promotional_price if self.is_en_promo else self.daily_price

    @property
    def remise_pct(self):
        if self.is_en_promo:
            return int(round((1 - float(self.promotional_price) / float(self.daily_price)) * 100))
        return 0


class CarImage(models.Model):
    car          = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images', verbose_name="Véhicule")
    image        = models.ImageField(upload_to='voiture/images/', verbose_name="Photo")
    principale   = models.BooleanField(default=False, verbose_name="Photo principale")
    ordre        = models.PositiveSmallIntegerField(default=0, verbose_name="Ordre d'affichage")
    description  = models.CharField(max_length=255, blank=True, verbose_name="Légende")
    date_ajout   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['ordre', 'date_ajout']
        verbose_name        = "Photo du véhicule"
        verbose_name_plural = "Photos du véhicule"

    def __str__(self):
        return f"{self.car} — photo {self.ordre + 1}"

    def save(self, *args, **kwargs):
        if self.principale:
            CarImage.objects.filter(car=self.car, principale=True).exclude(pk=self.pk).update(principale=False)
        super().save(*args, **kwargs)


class CarAvailability(models.Model):
    """Plages de dates pendant lesquelles le véhicule est disponible à la location."""
    car            = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="availabilities")
    available_from = models.DateField(verbose_name="Disponible du")
    available_to   = models.DateField(verbose_name="Au")

    class Meta:
        verbose_name        = "Plage de disponibilité"
        verbose_name_plural = "Plages de disponibilité"

    def __str__(self):
        return f"{self.car}: {self.available_from} → {self.available_to}"


class Reservation(models.Model):
    """Réservation d'un véhicule par un client."""

    STATUS_CHOICES = (
        ('pending',   'En attente'),
        ('confirmed', 'Confirmée'),
        ('cancelled', 'Annulée'),
        ('completed', 'Terminée'),
    )

    car    = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='reservations', verbose_name="Véhicule")
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations_voiture',
        verbose_name="Client"
    )

    date_debut   = models.DateField(verbose_name="Date de début")
    date_fin     = models.DateField(verbose_name="Date de fin")
    nombre_jours = models.PositiveIntegerField(verbose_name="Nombre de jours")
    prix_total   = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Prix total (FCFA)")

    statut         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    message_client = models.TextField(blank=True, verbose_name="Message du client")
    telephone      = models.CharField(max_length=20, blank=True, verbose_name="Téléphone de contact")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Réservation"
        verbose_name_plural = "Réservations"
        ordering            = ['-created_at']

    def __str__(self):
        nom = self.client.get_full_name() or self.client.username
        return f"Résa #{self.pk} — {self.car} · {nom} ({self.date_debut}→{self.date_fin})"

    @property
    def duree(self):
        return (self.date_fin - self.date_debut).days

    def is_cancellable(self):
        return self.statut in ('pending', 'confirmed')
