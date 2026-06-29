from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.templatetags.static import static

class User(AbstractUser):
    ROLES = [
        ('client', 'Client'),
        ('admin', 'Administrateur'),
        ('employe', 'Employé'),
        ('livreur', 'Livreur'),
        ('vendeur', 'Vendeur'),
    ]
    role = models.CharField(max_length=20, choices=ROLES, default='client')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    langue = models.CharField(max_length=5, choices=[('fr', 'Français'), ('en', 'Anglais')], default='fr')
    pays = models.CharField(max_length=100, blank=True, null=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    verified = models.BooleanField(default=False)
    statut = models.BooleanField(default=True)
    fcm_token = models.CharField(max_length=512, blank=True, null=True)
    matricule = models.CharField(max_length=30, blank=True, null=True, verbose_name='Matricule')
    last_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    last_lng = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    last_location = models.PointField(geography=True, null=True, blank=True)
    location_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def is_client(self):
        return self.role == 'client'

    def is_employe(self):
        return self.role == 'employe'

    def is_admin(self):
        return self.role == 'admin'

    def is_vendeur(self):
        return self.role == 'vendeur'

    def total_commandes(self):
        from resto.models import Order
        return Order.objects.filter(user=self).count()

    def save(self, *args, **kwargs):
        if self.telephone:
            self.telephone = self.telephone.replace(" ", "").replace("-", "")
        self.username = self.username.lower()
        super().save(*args, **kwargs)
    
    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return static('images/default-avatar.png')

    class Meta:
        ordering = ['-date_inscription']
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"


# ──────────────────────────────────────────────────────────────────────────────
# Profil Vendeur
# ──────────────────────────────────────────────────────────────────────────────
class VendeurProfile(models.Model):
    SECTIONS = [
        ('resto',        'Restaurant'),
        ('marche',       'Marché'),
        ('shopping',     'Shopping'),
        ('perruque',     'Perruque & Beauté'),
        ('voiture',      'Location Voiture'),
        ('immobilier',   'Immobilier'),
        ('quicaillerie', 'Quincaillerie'),
    ]

    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='vendeur_profile',
    )
    section = models.CharField(max_length=30, choices=SECTIONS, verbose_name='Section')

    # Infos commerciales
    nom_commercial  = models.CharField(max_length=200, blank=True, verbose_name='Nom commercial')
    description     = models.TextField(blank=True, verbose_name='Description')
    logo            = models.ImageField(upload_to='vendeurs/logos/', blank=True, null=True)
    telephone_pro   = models.CharField(max_length=20, blank=True, verbose_name='Téléphone professionnel')
    email_pro       = models.EmailField(blank=True, verbose_name='Email professionnel')
    site_web        = models.URLField(blank=True, verbose_name='Site web')

    # Statistiques (mises à jour périodiquement)
    note_moyenne      = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_ventes      = models.PositiveIntegerField(default=0)
    chiffre_affaires  = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    actif           = models.BooleanField(default=True, verbose_name='Actif')
    date_creation   = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profil Vendeur'
        verbose_name_plural = 'Profils Vendeurs'
        ordering = ['-date_creation']

    def __str__(self):
        return f'{self.user.get_full_name()} — {self.get_section_display()}'

    @property
    def section_label(self):
        return dict(self.SECTIONS).get(self.section, self.section)

    @property
    def section_icon(self):
        icons = {
            'resto': '🍽️', 'marche': '🛒', 'shopping': '🛍️',
            'perruque': '💇', 'voiture': '🚗',
            'immobilier': '🏢', 'quicaillerie': '🔨',
        }
        return icons.get(self.section, '🏪')

    @property
    def section_color(self):
        colors = {
            'resto': '#FF7A00', 'marche': '#16A34A', 'shopping': '#7C3AED',
            'perruque': '#EC4899', 'voiture': '#2563EB',
            'immobilier': '#4338CA', 'quicaillerie': '#EA580C',
        }
        return colors.get(self.section, '#6B7280')


# ──────────────────────────────────────────────────────────────────────────────
# Paiement générique (toutes sections)
# ──────────────────────────────────────────────────────────────────────────────
class Paiement(models.Model):
    STATUTS = [
        ('en_attente', 'En attente'),
        ('valide',     'Validé'),
        ('echoue',     'Échoué'),
        ('rembourse',  'Remboursé'),
        ('annule',     'Annulé'),
    ]
    METHODES = [
        ('especes',       'Espèces'),
        ('airtel_money',  'Airtel Money'),
        ('mtn_mobile',    'MTN Mobile Money'),
        ('orange_money',  'Orange Money'),
        ('carte',         'Carte bancaire'),
        ('virement',      'Virement bancaire'),
        ('autre',         'Autre'),
    ]
    SECTIONS = [
        ('resto',        'Restaurant'),
        ('marche',       'Marché'),
        ('shopping',     'Shopping'),
        ('perruque',     'Perruque'),
        ('voiture',      'Location Voiture'),
        ('immobilier',   'Immobilier'),
        ('quicaillerie', 'Quincaillerie'),
    ]

    # Qui paie
    client  = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='paiements', verbose_name='Client',
    )
    section = models.CharField(max_length=20, choices=SECTIONS, verbose_name='Section')

    # Lien générique vers n'importe quelle commande / réservation
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Type de commande',
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='ID commande')
    commande  = GenericForeignKey('content_type', 'object_id')

    # Montants
    montant          = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='Sous-total')
    frais_livraison  = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Frais livraison')
    frais_service    = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Frais service')
    montant_total    = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='Total')

    # Paiement
    methode             = models.CharField(max_length=30, choices=METHODES, default='especes', verbose_name='Méthode')
    telephone_paiement  = models.CharField(max_length=20, blank=True, verbose_name='Téléphone mobile money')
    fournisseur         = models.CharField(max_length=60, blank=True, verbose_name='Fournisseur')
    reference_externe   = models.CharField(max_length=200, blank=True, verbose_name='Référence externe')
    statut              = models.CharField(max_length=20, choices=STATUTS, default='en_attente', verbose_name='Statut')

    # Livraison
    mode_livraison     = models.CharField(
        max_length=20,
        choices=[('livraison', 'Livraison'), ('retrait', 'Retrait en boutique')],
        default='livraison', verbose_name='Mode',
    )
    quartier_livraison = models.CharField(max_length=100, blank=True, verbose_name='Quartier')
    adresse_livraison  = models.TextField(blank=True, verbose_name='Adresse exacte')
    gps_lat            = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name='GPS Latitude')
    gps_lng            = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, verbose_name='GPS Longitude')
    statut_preparation = models.CharField(
        max_length=20,
        choices=[('recu', 'Reçu'), ('en_preparation', 'En préparation'), ('pret', 'Prêt à livrer')],
        default='recu', verbose_name='Préparation',
    )

    # Timestamps
    cree_le      = models.DateTimeField(auto_now_add=True)
    valide_le    = models.DateTimeField(null=True, blank=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True, verbose_name='Notes internes')

    class Meta:
        ordering = ['-cree_le']
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['section', '-cree_le']),
            models.Index(fields=['client', '-cree_le']),
        ]

    def __str__(self):
        client = self.client.get_full_name() if self.client else 'Anonyme'
        return f'Paiement #{self.pk} — {client} — {self.montant_total} FCFA ({self.get_statut_display()})'

    @property
    def statut_color(self):
        colors = {
            'en_attente': 'yellow', 'valide': 'green',
            'echoue': 'red', 'rembourse': 'blue', 'annule': 'gray',
        }
        return colors.get(self.statut, 'gray')


# ──────────────────────────────────────────────────────────────────────────────
# Livraison — flux complet vendeur → livreur → client
# ──────────────────────────────────────────────────────────────────────────────
class Livraison(models.Model):
    STATUTS = [
        ('attente_livreur', 'En attente de livreur'),
        ('assigne',         'Livreur assigné'),
        ('accepte',         'Accepté par le livreur'),
        ('en_recuperation', 'En récupération'),
        ('en_route',        'En route vers le client'),
        ('livree',          'Livrée'),
        ('echouee',         'Échouée'),
    ]

    paiement    = models.OneToOneField(
        Paiement, on_delete=models.CASCADE, related_name='livraison',
    )
    livreur     = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='missions_livraison',
    )
    livreur_nom_cache = models.CharField(max_length=200, blank=True, verbose_name='Nom livreur (cache)')
    statut      = models.CharField(max_length=30, choices=STATUTS, default='attente_livreur')
    otp_code    = models.CharField(max_length=6, blank=True, verbose_name='Code OTP')
    otp_valide  = models.BooleanField(default=False)

    assigned_at  = models.DateTimeField(null=True, blank=True)
    accepted_at  = models.DateTimeField(null=True, blank=True)
    picked_at    = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Livraison'
        verbose_name_plural = 'Livraisons'
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['livreur', 'statut']),
        ]

    def __str__(self):
        livreur = self.livreur.get_full_name() if self.livreur else 'non assigné'
        return f'Livraison #{self.pk} — {livreur} — {self.get_statut_display()}'


# ──────────────────────────────────────────────────────────────────────────────
# Historique des positions GPS (trail de déplacement)
# ──────────────────────────────────────────────────────────────────────────────
class UserPositionLog(models.Model):
    """Stocke les dernières positions GPS de chaque utilisateur (max 50 par user)."""
    user        = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='position_logs',
    )
    lat         = models.DecimalField(max_digits=10, decimal_places=8)
    lng         = models.DecimalField(max_digits=11, decimal_places=8)
    position    = models.PointField(srid=4326, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
        indexes  = [models.Index(fields=['user', '-recorded_at'])]
        verbose_name        = 'Log position'
        verbose_name_plural = 'Logs positions'

    def __str__(self):
        return f'{self.user} — {self.lat},{self.lng} @ {self.recorded_at:%H:%M:%S}'
