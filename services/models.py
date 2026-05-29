from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone


class ServiceCategory(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon_name = models.CharField(
        max_length=50,
        blank=True,  # Non obligatoire
        null=True,
        help_text="Nom de l’icône Material Symbols (ex : 'groups', 'settings', 'home')"
    )
    ordre_affichage = models.PositiveIntegerField(default=0, help_text="Ordre d’affichage sur le site/app")
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordre_affichage', 'nom']
        verbose_name = "Catégorie de service"
        verbose_name_plural = "Catégories de services"

    def __str__(self):
        return self.nom

    # ✅ Génération automatique du slug à la sauvegarde
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    # ✅ Méthode pratique pour le front-end (URL de la catégorie)
    def get_absolute_url(self):
        return reverse('services:category_detail', args=[self.slug])

    # ✅ Retourne le nombre de services actifs dans la catégorie
    def total_services_actifs(self):
        return self.services.filter(actif=True).count()
    
    @property
    def display_image(self):
        """
        Retourne le HTML d’une image ou d’une icône selon la disponibilité.
        """
        if self.image:
            return f'<img src="{self.image.url}" alt="{self.nom}" class="w-10 h-10 object-cover rounded-lg">'
        elif self.icon_name:
            return f'<span class="material-symbols-outlined text-3xl">{self.icon_name}</span>'
        return '<span class="text-slate-400 italic">Aucune image</span>'

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    nom = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField()
    avantages = models.TextField(blank=True, help_text="Liste des avantages ou détails marketing du service")
    prix_base = models.DecimalField(max_digits=10, decimal_places=2)
    remise = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Pourcentage de réduction (0-100)")
    delai_moyen = models.IntegerField(help_text="Durée moyenne en jours")
    actif = models.BooleanField(default=True)
    populaire = models.BooleanField(default=False, help_text="Afficher ce service en avant sur la page d’accueil")
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    icon_name = models.CharField(
        max_length=50,
        blank=True,  # Non obligatoire
        null=True,
        help_text="Nom de l’icône Material Symbols (ex : 'groups', 'settings', 'home')"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-populaire', 'nom']
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return self.nom

    # ✅ Génération automatique du slug à la sauvegarde
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nom)
            # Gérer les doublons possibles
            unique_slug = base_slug
            count = 1
            while Service.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{count}"
                count += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    # ✅ Retourne l’URL du détail du service
    def get_absolute_url(self):
        return reverse('services:service_detail', args=[self.slug])

    # ✅ Prix final après remise
    def prix_final(self):
        return round(self.prix_base * (1 - (self.remise / 100)), 2)

    # ✅ Vérifie si le service est encore actif
    def est_disponible(self):
        return self.actif and self.category.actif

    # ✅ Durée estimée sous forme lisible
    def delai_estime(self):
        if self.delai_moyen <= 1:
            return f"{self.delai_moyen} jour"
        return f"{self.delai_moyen} jours"

    # ✅ Affiche si le service est récent
    def est_recent(self):
        return (timezone.now() - self.date_creation).days < 30
    
    @property
    def display_image(self):
        """
        Retourne le HTML d’une image ou d’une icône selon la disponibilité.
        """
        if self.image:
            return f'<img src="{self.image.url}" alt="{self.nom}" class="w-10 h-10 object-cover rounded-lg">'
        elif self.icon_name:
            return f'<span class="material-symbols-outlined text-3xl">{self.icon_name}</span>'
        return '<span class="text-slate-400 italic">Aucune image</span>'


class ServiceImage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='services/extra/', blank=True, null=True)
    titre = models.CharField(max_length=150, blank=True, null=True)
    ordre = models.PositiveIntegerField(default=0, help_text="Ordre d’affichage")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Image associée"
        verbose_name_plural = "Images associées"

    def __str__(self):
        return f"Image de {self.service.nom} ({self.titre or 'Sans titre'})"

    @property
    def preview(self):
        if self.image:
            return f'<img src="{self.image.url}" width="80" style="border-radius:6px;object-fit:cover;">'
        return '<span class="text-slate-400 italic">Aucune image</span>'

class ServiceTexte(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='textes')
    titre = models.CharField(max_length=150, blank=True, null=True)
    contenu = models.TextField()
    nombre_documents = models.PositiveIntegerField(default=1, help_text="Nombre de documents à traiter")
    prix = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="Prix spécifique pour ce pack")
    ordre = models.PositiveIntegerField(default=0, help_text="Ordre d’affichage du texte")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Texte associé"
        verbose_name_plural = "Textes associés"

    def __str__(self):
        return f"{self.titre or 'Pack'} ({self.prix} €)"

    def get_absolute_url(self):
        return reverse('services:detail', args=[self.service.slug])




