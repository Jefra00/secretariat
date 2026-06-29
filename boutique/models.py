from django.contrib.gis.db import models
from django.conf import settings


class BoutiqueQuerySet(models.QuerySet):
    def actives(self):
        return self.filter(actif=True)

    def pour_user(self, user):
        return self.filter(user=user)


class BoutiqueManager(models.Manager):
    def get_queryset(self):
        return BoutiqueQuerySet(self.model, using=self._db)

    def actives(self):
        return self.get_queryset().actives()


class Boutique(models.Model):
    TYPE_COMMERCE = [
        ('marche',        'Faire le marché'),
        ('shopping',      'Shopping'),
        ('quincaillerie', 'Quincaillerie'),
        ('perruque',      'Perruques & beauté'),
        ('electronique',  'Électronique'),
        ('mode',          'Mode'),
        ('pharmacie',     'Pharmacie'),
        ('restaurant',    'Restaurant'),
        ('elevage',       'Élevage'),
        ('voiture',       'Location voiture'),
        ('immobilier',    'Immobilier'),
        ('autre',         'Autre'),
    ]

    # ── Identité ─────────────────────────────────────────────────────────────
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mes_boutiques',
        verbose_name='Propriétaire',
    )
    nom         = models.CharField(max_length=200, verbose_name='Nom de la boutique')
    telephone   = models.CharField(max_length=20, blank=True, verbose_name='Téléphone boutique')
    description = models.TextField(blank=True, verbose_name='Description')
    logo        = models.ImageField(
        upload_to='boutiques/logos/',
        null=True, blank=True,
        verbose_name='Logo',
    )

    # ── Localisation ─────────────────────────────────────────────────────────
    ville = models.ForeignKey(
        'location.Ville',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='boutiques', verbose_name='Ville',
    )
    commune = models.ForeignKey(
        'location.Commune',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='boutiques', verbose_name='Commune',
    )
    quartier = models.ForeignKey(
        'location.Quartier',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='boutiques', verbose_name='Quartier',
    )
    marche = models.ForeignKey(
        'marche.Marche',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='boutiques', verbose_name='Marché',
    )
    type_commerce = models.CharField(
        max_length=30, choices=TYPE_COMMERCE, blank=True,
        verbose_name='Type de commerce',
    )
    adresse_exacte = models.CharField(
        max_length=300, blank=True,
        verbose_name='Adresse exacte',
    )
    position = models.PointField(
        null=True, blank=True, srid=4326,
        verbose_name='Position GPS',
        help_text='Cliquez sur la carte pour placer la boutique',
    )

    # ── Statut ───────────────────────────────────────────────────────────────
    actif = models.BooleanField(
        default=True,
        verbose_name='Active',
        help_text='Décocher pour bloquer et masquer tous les produits',
    )
    raison_blocage = models.TextField(
        blank=True,
        verbose_name='Raison du blocage',
    )

    # ── Timestamps ───────────────────────────────────────────────────────────
    cree_le    = models.DateTimeField(auto_now_add=True)
    mis_a_jour = models.DateTimeField(auto_now=True)

    objects = BoutiqueManager()

    class Meta:
        ordering     = ['-cree_le']
        verbose_name = 'Boutique'
        verbose_name_plural = 'Boutiques'
        indexes = [
            models.Index(fields=['actif']),
            models.Index(fields=['user', 'actif']),
            models.Index(fields=['ville', 'commune']),
        ]

    def __str__(self):
        ville = self.ville.nom if self.ville else '—'
        return f'{self.nom} ({ville})'

    # ── Alias pour compatibilité templates ───────────────────────────────────
    @property
    def name(self):
        return self.nom

    @property
    def nom_boutique(self):
        return self.nom

    @property
    def contact_telephone(self):
        """Téléphone de contact : celui de la boutique, sinon celui du propriétaire."""
        return self.telephone or (self.user.telephone if self.user_id else '')

    @property
    def position_geojson(self):
        return self.position.geojson if self.position else None

    @property
    def position_lat(self):
        return self.position.y if self.position else None

    @property
    def position_lng(self):
        return self.position.x if self.position else None
