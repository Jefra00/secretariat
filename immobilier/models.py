from django.db import models
from django.conf import settings


class ImmobilierCategory(models.Model):
    nom  = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Icône emoji")

    class Meta:
        verbose_name        = "Catégorie immobilier"
        verbose_name_plural = "Catégories immobilier"
        ordering            = ['nom']

    def __str__(self):
        return f"{self.icon} {self.nom}".strip()


class Immobilier(models.Model):

    TYPE_BIEN = (
        ("maison",      "Maison"),
        ("appartement", "Appartement"),
        ("studio",      "Studio"),
        ("villa",       "Villa"),
        ("terrain",     "Terrain"),
        ("bureau",      "Bureau"),
        ("commerce",    "Local commercial"),
        ("entrepot",    "Entrepôt"),
    )
    TYPE_OFFRE = (
        ("vente",    "Vente"),
        ("location", "Location"),
    )
    STATUT = (
        ("disponible", "Disponible"),
        ("reserve",    "Réservé"),
        ("vendu",      "Vendu"),
        ("loue",       "Loué"),
    )

    # ── Propriétaire & catégorie ──────────────────────────────────────────────
    vendeur = models.ForeignKey(
        'boutique.Boutique',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="biens",
        verbose_name="Agence / Propriétaire",
    )
    categorie = models.ForeignKey(
        ImmobilierCategory,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="biens",
        verbose_name="Catégorie",
    )

    # ── Identité du bien ──────────────────────────────────────────────────────
    titre      = models.CharField(max_length=255, verbose_name="Titre")
    type_bien  = models.CharField(max_length=30, choices=TYPE_BIEN, verbose_name="Type de bien")
    type_offre = models.CharField(max_length=20, choices=TYPE_OFFRE, verbose_name="Type d'offre")
    statut     = models.CharField(max_length=20, choices=STATUT, default="disponible", verbose_name="Statut")

    # ── Prix & promotion ──────────────────────────────────────────────────────
    prix              = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Prix (FCFA)")
    prix_promotionnel = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name="Prix promotionnel (FCFA)",
    )
    promo_debut = models.DateField(null=True, blank=True, verbose_name="Début promotion")
    promo_fin   = models.DateField(null=True, blank=True, verbose_name="Fin promotion")

    # ── Caractéristiques du bien ──────────────────────────────────────────────
    superficie         = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Superficie (m²)")
    nombre_chambres    = models.PositiveIntegerField(default=0, verbose_name="Chambres")
    nombre_salles_bain = models.PositiveIntegerField(default=0, verbose_name="Salles de bain")
    nombre_salons      = models.PositiveIntegerField(default=0, verbose_name="Salons")
    nombre_cuisines    = models.PositiveIntegerField(default=0, verbose_name="Cuisines")
    nombre_garages     = models.PositiveIntegerField(default=0, verbose_name="Garages")
    etage              = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name="Étage (appartement)",
        help_text="Laisser vide pour maison / villa / terrain.",
    )
    annee_construction = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Année de construction",
    )
    meuble = models.BooleanField(default=False, verbose_name="Meublé")

    # ── Équipements & commodités ──────────────────────────────────────────────
    piscine      = models.BooleanField(default=False, verbose_name="Piscine")
    parking      = models.BooleanField(default=False, verbose_name="Parking")
    gardien      = models.BooleanField(default=False, verbose_name="Gardien")
    wifi         = models.BooleanField(default=False, verbose_name="Wi-Fi")
    climatisation = models.BooleanField(default=False, verbose_name="Climatisation")
    generatrice  = models.BooleanField(default=False, verbose_name="Groupe électrogène")
    eau_courante = models.BooleanField(default=True,  verbose_name="Eau courante")

    # ── Localisation ──────────────────────────────────────────────────────────
    ville   = models.ForeignKey(
        'location.Ville',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="ville",
        verbose_name="Agence / Propriétaire",
    )
    quartier = models.ForeignKey(
        'location.Quartier',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="quartier",
        verbose_name="Agence / Propriétaire",
    )
    caution   = models.CharField(max_length=100, verbose_name="caution (ex: 1 mois de loyer)", blank=True)
    

    # ── Description ───────────────────────────────────────────────────────────
    description = models.TextField(verbose_name="Description")

    # ── Dates système ─────────────────────────────────────────────────────────
    date_creation     = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True,     verbose_name="Date de modification")

    class Meta:
        verbose_name        = "Bien immobilier"
        verbose_name_plural = "Biens immobiliers"
        ordering            = ['-date_creation']

    def __str__(self):
        return self.titre

    # ── Propriétés promo ──────────────────────────────────────────────────────
    @property
    def is_en_promo(self):
        from datetime import date
        if not self.prix_promotionnel or self.prix_promotionnel >= self.prix:
            return False
        today = date.today()
        if self.promo_debut and self.promo_debut > today:
            return False
        if self.promo_fin and self.promo_fin < today:
            return False
        return True

    @property
    def prix_actuel(self):
        return self.prix_promotionnel if self.is_en_promo else self.prix

    @property
    def remise_pct(self):
        if self.is_en_promo:
            return int(round((1 - float(self.prix_promotionnel) / float(self.prix)) * 100))
        return 0

    @property
    def suffix_prix(self):
        return "/mois" if self.type_offre == "location" else ""


class PhotoImmobilier(models.Model):
    bien       = models.ForeignKey(Immobilier, on_delete=models.CASCADE, related_name="photos")
    image      = models.ImageField(upload_to="immobilier/photos/", verbose_name="Photo")
    principale = models.BooleanField(default=False, verbose_name="Photo principale")
    ordre      = models.PositiveSmallIntegerField(default=0, verbose_name="Ordre d'affichage")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['ordre', 'date_creation']
        verbose_name        = "Photo du bien"
        verbose_name_plural = "Photos du bien"

    def __str__(self):
        return f"Photo — {self.bien.titre}"

    def save(self, *args, **kwargs):
        if self.principale:
            PhotoImmobilier.objects.filter(bien=self.bien, principale=True).exclude(pk=self.pk).update(principale=False)
        super().save(*args, **kwargs)


class VideoImmobilier(models.Model):
    bien  = models.OneToOneField(Immobilier, on_delete=models.CASCADE, related_name="video")
    video = models.FileField(upload_to="immobilier/videos/", verbose_name="Vidéo")

    def __str__(self):
        return f"Vidéo — {self.bien.titre}"


class DemandeVisite(models.Model):
    STATUT = (
        ('pending',   'En attente'),
        ('confirmed', 'Confirmée'),
        ('cancelled', 'Annulée'),
        ('done',      'Effectuée'),
    )

    bien          = models.ForeignKey(Immobilier, on_delete=models.CASCADE, related_name='demandes_visite', verbose_name="Bien")
    client        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='demandes_visite_immo',
        verbose_name="Client",
    )
    date_souhaitee  = models.DateField(verbose_name="Date souhaitée")
    heure_souhaitee = models.TimeField(null=True, blank=True, verbose_name="Heure souhaitée")
    telephone       = models.CharField(max_length=20, verbose_name="Téléphone de contact")
    message         = models.TextField(blank=True, verbose_name="Message")
    statut          = models.CharField(max_length=20, choices=STATUT, default='pending', verbose_name="Statut")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Demande de visite"
        verbose_name_plural = "Demandes de visite"
        ordering            = ['-created_at']

    def __str__(self):
        nom = self.client.get_full_name() or self.client.username
        return f"Visite #{self.pk} — {self.bien.titre} · {nom} ({self.date_souhaitee})"
