from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
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


class WigProduct(models.Model):

    STATUS_CHOICES = (
        ("available", "Disponible"),
        ("out_of_stock", "Rupture de stock"),
        ("preorder", "Précommande"),
    )

    MATERIAL_CHOICES = (
        ("natural", "Naturelle"),
        ("synthetic", "Synthétique"),
    )

    TEXTURE_CHOICES = (
        ("straight", "Lisse"),
        ("curly", "Bouclée"),
        ("wavy", "Ondulée"),
        ("kinky", "Kinky"),
        ("body_wave", "Body Wave"),
        ("deep_wave", "Deep Wave"),
    )

    name = models.CharField(
        max_length=255,
        verbose_name="Nom du produit"
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Prix"
    )

    shop = models.ForeignKey(
        'boutique.Boutique',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="product"
    )

    promotional_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Prix promotionnel"
    )

    promo_debut = models.DateField(null=True, blank=True, verbose_name="Début promotion")
    promo_fin   = models.DateField(null=True, blank=True, verbose_name="Fin promotion")

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    description = models.TextField(
        verbose_name="Description"
    )

    color = models.CharField(
        max_length=100,
        null=True, blank=True,
        verbose_name="Couleur"
    )

    length = models.CharField(
        max_length=50,
        help_text='Exemple : 10", 12", 14"',
        verbose_name="Longueur"
    )

    texture = models.CharField(
        max_length=30,
        choices=TEXTURE_CHOICES,
        verbose_name="Texture"
    )

    material = models.CharField(
        max_length=20,
        choices=MATERIAL_CHOICES,
        verbose_name="Matière"
    )

    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantité en stock"
    )

    video = models.FileField(
        upload_to="wigs/videos/",
        null=True,
        blank=True,
        verbose_name="Vidéo de présentation"
    )

    city = models.CharField(
        max_length=150,
        verbose_name="Ville"
    )

    location = models.CharField(
        max_length=255,
        verbose_name="Localisation"
    )

    delivery_available = models.BooleanField(
        default=True,
        verbose_name="Livraison disponible"
    )

    average_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5)
        ],
        verbose_name="Note moyenne"
    )

    reviews_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre d'avis"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available",
        verbose_name="Statut"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    @property
    def is_en_promo(self):
        from datetime import date
        if not self.promotional_price or self.promotional_price >= self.price:
            return False
        today = date.today()
        if self.promo_debut and self.promo_debut > today:
            return False
        if self.promo_fin and self.promo_fin < today:
            return False
        return True

    @property
    def prix_actuel(self):
        return self.promotional_price if self.is_en_promo else self.price

    @property
    def remise_pct(self):
        if self.is_en_promo:
            return int(round((1 - float(self.promotional_price) / float(self.price)) * 100))
        return 0

    def __str__(self):
        return self.name


class ProductImage(models.Model):

    product = models.ForeignKey(
        WigProduct,
        on_delete=models.CASCADE,
        related_name='images'
    )

    couleur = models.ForeignKey(
        'shopping.Couleur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='image'
    )

    tailles = models.ManyToManyField(
        'shopping.Taille',
        blank=True,
        related_name='product'
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