from django.db import models

class CategorieQuincaillerie(models.Model):

    nom = models.CharField(
        max_length=150,
        unique=True
    )

    icone = models.CharField(
        max_length=100,
        blank=True
    )

    categorie_parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.nom


class ProduitQuincaillerie(models.Model):

    ETAT = (
        ("neuf", "Neuf"),
        ("occasion", "Occasion"),
    )

    STATUT = (
        ("disponible", "Disponible"),
        ("rupture", "Rupture de stock"),
        ("precommande", "Précommande"),
    )


    boutique = models.ForeignKey(
        "boutique.Boutique",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="produits_quincaillerie"
    )

    categorie = models.ForeignKey(
        "CategorieQuincaillerie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    nom = models.CharField(
        max_length=255,
        verbose_name="Nom du produit"
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Référence"
    )

    marque = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Marque"
    )

    prix = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    prix_promotionnel = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    description = models.TextField()

    unite = models.CharField(
        max_length=50,
        default="Pièce"
    )

    quantite_stock = models.PositiveIntegerField(
        default=0
    )

    etat = models.CharField(
        max_length=20,
        choices=ETAT,
        default="neuf"
    )

    poids = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    garantie = models.CharField(
        max_length=100,
        blank=True
    )

    livraison_disponible = models.BooleanField(
        default=True
    )

    ville = models.CharField(
        max_length=100
    )

    adresse = models.CharField(
        max_length=255
    )


    statut = models.CharField(
        max_length=20,
        choices=STATUT,
        default="disponible"
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    date_modification = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.nom

    @property
    def is_en_promo(self):
        return bool(self.prix_promotionnel and self.prix_promotionnel < self.prix)

    @property
    def prix_actuel(self):
        if self.is_en_promo:
            return self.prix_promotionnel
        return self.prix

    @property
    def remise_pct(self):
        if self.is_en_promo:
            return round((1 - self.prix_promotionnel / self.prix) * 100)
        return 0


class ProductImage(models.Model):

    produit = models.ForeignKey(
        ProduitQuincaillerie,
        on_delete=models.CASCADE,
        related_name='images'
    )

    couleur = models.ForeignKey(
        'shopping.Couleur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='image_quincaillerie'
    )

    tailles = models.ManyToManyField(
        'shopping.Taille',
        blank=True,
        related_name='product_quincaillerie'
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
        return f"{self.produit.nom}{couleur}"

    def save(self, *args, **kwargs):
        if self.principale:
            ProductImage.objects.filter(
                produit=self.produit,
                principale=True
            ).exclude(
                pk=self.pk
            ).update(principale=False)
        super().save(*args, **kwargs)