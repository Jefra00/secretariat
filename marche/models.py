import uuid
from django.conf import settings
from django.contrib.gis.db import models   # ← GIS pour PointField
from django.utils.text import slugify


class TypeCommerce(models.TextChoices):
    MARCHE        = 'marche',        'Faire le marché'
    SHOPPING      = 'shopping',      'Shopping'
    QUINCAILLERIE = 'quincaillerie', 'Quincaillerie'
    PERRUQUES     = 'perruques',     'Perruques & beauté'
    ELECTRONIQUE  = 'electronique',  'Électronique'
    MODE          = 'mode',          'Mode'
    PHARMACIE     = 'pharmacie',     'Pharmacie'
    RESTAURANT    = 'restaurant',    'Restaurant'
    ELEVAGE       = 'elevage',       'Élevage'
    AUTRE         = 'autre',         'Autre'


class Categorie(models.Model):
    nom   = models.CharField(max_length=100, unique=True)
    slug  = models.SlugField(max_length=120, unique=True, blank=True)
    emoji = models.CharField(max_length=10, blank=True)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'

    def __str__(self):
        return f'{self.emoji} {self.nom}' if self.emoji else self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)


class Marche(models.Model):
    nom      = models.CharField(max_length=200)
    ville    = models.ForeignKey(
        'location.Ville', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='marches'
    )
    commune  = models.ForeignKey(
        'location.Commune', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='marches'
    )
    quartier = models.ForeignKey(
        'location.Quartier', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='marches'
    )
    position = models.PointField(
        null=True, blank=True, srid=4326,
        help_text='Position GPS du marché (point central)'
    )
    actif         = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Marché'
        verbose_name_plural = 'Marchés'

    def __str__(self):
        ville = self.ville.nom if self.ville else '—'
        return f'{self.nom} — {ville}'

    @property
    def position_geojson(self):
        return self.position.geojson if self.position else None


class Vendeur(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, related_name='boutiques'
    )
    nom_boutique  = models.CharField(max_length=200)
    type_commerce = models.CharField(
        max_length=50, choices=TypeCommerce.choices, default=TypeCommerce.MARCHE
    )
    ville    = models.ForeignKey(
        'location.Ville', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='vendeurs'
    )
    commune  = models.ForeignKey(
        'location.Commune', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='vendeurs'
    )
    quartier = models.ForeignKey(
        'location.Quartier', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='vendeurs'
    )
    marche    = models.ForeignKey(
        Marche, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='vendeurs'
    )
    nom_marche = models.CharField(max_length=200, blank=True, help_text='Si marché non listé')
    stand      = models.CharField(max_length=100, blank=True)
    position   = models.PointField(
        null=True, blank=True, srid=4326,
        help_text='Position GPS du stand / de la boutique'
    )
    logo        = models.ImageField(upload_to='marche/vendeurs/', blank=True, null=True)
    description = models.TextField(blank=True)
    boutique    = models.ForeignKey(
        'boutique.Boutique',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='vendeurs_marche',
        verbose_name='Boutique (nouveau système)',
    )
    verified    = models.BooleanField(default=False)
    actif       = models.BooleanField(default=True)
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_inscription']
        verbose_name = 'Vendeur'
        verbose_name_plural = 'Vendeurs'

    def __str__(self):
        return f'{self.nom_boutique} ({self.get_type_commerce_display()})'

    def nombre_produits(self):
        return self.produits.filter(disponibilite=True).count()

    @property
    def position_geojson(self):
        return self.position.geojson if self.position else None


class Couleur(models.Model):
    nom      = models.CharField(max_length=100, unique=True)
    code_hex = models.CharField(
        max_length=7, blank=True,
        help_text='Code hexadécimal, ex : #FF0000'
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Couleur'
        verbose_name_plural = 'Couleurs'

    def __str__(self):
        return self.nom


class Produit(models.Model):
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom       = models.CharField(max_length=200)
    categorie = models.ForeignKey(
        Categorie, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='produits'
    )
    prix        = models.DecimalField(max_digits=10, decimal_places=2)
    prix_promo  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix promotionnel")
    promo_debut = models.DateField(null=True, blank=True, verbose_name="Début promotion")
    promo_fin   = models.DateField(null=True, blank=True, verbose_name="Fin promotion")
    devise      = models.CharField(max_length=10, default='FCFA')
    unite       = models.CharField(max_length=50, default='pièce')
    description = models.TextField(blank=True)
    image       = models.ImageField(upload_to='marche/produits/', blank=True, null=True)
    vendeur     = models.ForeignKey(
        'boutique.Boutique',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='produits'
    )
    marche  = models.ForeignKey(
        Marche, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='produits'
    )
    ville = models.ForeignKey(
        'location.Ville', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='produits'
    )
    stock           = models.PositiveIntegerField(default=0)
    disponibilite   = models.BooleanField(default=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    date_creation   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_mise_a_jour']
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'

    def __str__(self):
        return f'{self.nom} — {self.prix} {self.devise}/{self.unite}'

    @property
    def is_en_promo(self):
        from datetime import date
        if not self.prix_promo or self.prix_promo >= self.prix:
            return False
        today = date.today()
        if self.promo_debut and self.promo_debut > today:
            return False
        if self.promo_fin and self.promo_fin < today:
            return False
        return True

    @property
    def prix_actuel(self):
        return self.prix_promo if self.is_en_promo else self.prix

    @property
    def remise_pct(self):
        if self.is_en_promo:
            return int(round((1 - float(self.prix_promo) / float(self.prix)) * 100))
        return 0

    @property
    def prix_affiche(self):
        return f'{self.prix:,.0f} {self.devise}/{self.unite}'

    @property
    def image_principale(self):
        """Retourne la première image (ordre=0 / principale=True), sinon le champ image."""
        img = self.images.filter(principale=True).order_by('ordre').first()
        if img:
            return img.image
        img = self.images.order_by('ordre').first()
        return img.image if img else self.image


class ProduitImage(models.Model):
    produit     = models.ForeignKey(
        Produit, on_delete=models.CASCADE, related_name='images'
    )
    couleur     = models.ForeignKey(
        Couleur, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='images',
        help_text='Couleur associée à cette vue du produit'
    )
    image       = models.ImageField(upload_to='marche/produits/images/')
    ordre       = models.PositiveSmallIntegerField(
        default=0, help_text='0 = affiché en premier'
    )
    principale  = models.BooleanField(
        default=False,
        help_text='Image mise en avant sur la fiche produit'
    )
    description = models.CharField(max_length=255, blank=True)
    date_ajout  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', 'date_ajout']
        verbose_name = 'Image produit'
        verbose_name_plural = 'Images produit'

    def __str__(self):
        couleur = f' — {self.couleur.nom}' if self.couleur else ''
        return f'{self.produit.nom}{couleur} (ordre {self.ordre})'

    def save(self, *args, **kwargs):
        # Une seule image principale par produit
        if self.principale:
            ProduitImage.objects.filter(
                produit=self.produit, principale=True
            ).exclude(pk=self.pk).update(principale=False)
        super().save(*args, **kwargs)
