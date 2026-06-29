from django.contrib.gis.db import models
from django.conf import settings


class Category(models.Model):

    name = models.CharField(max_length=150)

    icon = models.CharField(
        max_length=50,
        blank=True
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children"
    )

    def __str__(self):
        return self.name


class Vendor(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_vendors'
    )

    business_name = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name


class Shop(models.Model):

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="shops"
    )

    name = models.CharField(max_length=200)

    slug = models.SlugField(unique=True)

    logo = models.ImageField(
        upload_to="shops/",
        blank=True,
        null=True
    )

    description = models.TextField()

    address = models.CharField(max_length=255)

    ville = models.ForeignKey(
        'location.Ville',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shops'
    )

    commune = models.ForeignKey(
        'location.Commune',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shops'
    )

    quartier = models.ForeignKey(
        'location.Quartier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shops'
    )

    position = models.PointField(
        null=True,
        blank=True,
        srid=4326,
        help_text='Position GPS de la boutique'
    )

    boutique = models.ForeignKey(
        'boutique.Boutique',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shops',
        verbose_name='Boutique (nouveau système)',
    )

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):

    shop = models.ForeignKey(
        'boutique.Boutique',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="products"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    name = models.CharField(max_length=255)

    slug = models.SlugField(unique=True)

    description = models.TextField()

    price = models.DecimalField(max_digits=12, decimal_places=2)

    prix_promo = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True, verbose_name="Prix promotionnel"
    )
    promo_debut = models.DateField(null=True, blank=True, verbose_name="Début promotion")
    promo_fin   = models.DateField(null=True, blank=True, verbose_name="Fin promotion")

    stock = models.IntegerField(default=0)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_en_promo(self):
        from datetime import date
        if not self.prix_promo or self.prix_promo >= self.price:
            return False
        today = date.today()
        if self.promo_debut and self.promo_debut > today:
            return False
        if self.promo_fin and self.promo_fin < today:
            return False
        return True

    @property
    def prix_actuel(self):
        return self.prix_promo if self.is_en_promo else self.price

    @property
    def remise_pct(self):
        if self.is_en_promo:
            return int(round((1 - float(self.prix_promo) / float(self.price)) * 100))
        return 0

    def __str__(self):
        return self.name


class Taille(models.Model):

    nom = models.CharField(
        max_length=20,
        unique=True
    )

    description = models.CharField(
        max_length=100,
        blank=True
    )

    class Meta:
        ordering = ['nom']
        verbose_name = "Taille"
        verbose_name_plural = "Tailles"

    def __str__(self):
        return self.nom


class Couleur(models.Model):

    nom = models.CharField(
        max_length=100,
        unique=True
    )

    code_hex = models.CharField(
        max_length=7,
        blank=True,
        help_text='Ex: #FF0000'
    )

    description = models.TextField(blank=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Couleur'
        verbose_name_plural = 'Couleurs'

    def __str__(self):
        return self.nom


class ProductImage(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )

    couleur = models.ForeignKey(
        Couleur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='images'
    )

    tailles = models.ManyToManyField(
        Taille,
        blank=True,
        related_name='products'
    )

    image = models.ImageField(
        upload_to='shopping/products/images/'
    )

    ordre = models.PositiveSmallIntegerField(
        default=0,
        help_text='0 = image principale'
    )

    principale = models.BooleanField(
        default=False
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    date_ajout = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['ordre', 'date_ajout']
        verbose_name = 'Image produit'
        verbose_name_plural = 'Images produit'

    def __str__(self):
        couleur = f" - {self.couleur.nom}" if self.couleur else ""
        return f"{self.product.name}{couleur}"

    def save(self, *args, **kwargs):

        if self.principale:
            ProductImage.objects.filter(
                product=self.product,
                principale=True
            ).exclude(
                pk=self.pk
            ).update(principale=False)

        super().save(*args, **kwargs)