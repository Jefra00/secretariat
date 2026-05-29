from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
import uuid


class BlogPost(models.Model):
    """Article de blog publié sur la plateforme."""

    STATUTS = [
        ('brouillon', 'Brouillon'),
        ('publie', 'Publié'),
        ('archive', 'Archivé'),
    ]

    id_public = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='articles')
    titre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, editable=False)
    contenu = models.TextField()
    categorie = models.CharField(max_length=100, blank=True, null=True)
    image_couverture = models.ImageField(upload_to='blog/couvertures/', blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='brouillon')
    date_publication = models.DateTimeField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    vues = models.PositiveIntegerField(default=0)
    en_avant = models.BooleanField(default=False, help_text="Mettre en avant sur la page d'accueil")

    class Meta:
        ordering = ['-date_publication', '-date_creation']
        verbose_name = "Article de blog"
        verbose_name_plural = "Articles de blog"

    def __str__(self):
        return self.titre

    # ✅ Génération automatique du slug
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.titre}-{uuid.uuid4().hex[:8]}")
        if self.statut == 'publie' and not self.date_publication:
            self.date_publication = timezone.now()
        super().save(*args, **kwargs)

    # ✅ Nombre de jours depuis la publication
    def age_article(self):
        if not self.date_publication:
            return "Non publié"
        delta = timezone.now() - self.date_publication
        return f"{delta.days} jours"

    # ✅ Incrémentation du compteur de vues
    def incrementer_vues(self):
        self.vues += 1
        self.save(update_fields=['vues'])

    # ✅ Raccourci pour le contenu
    def extrait(self):
        return self.contenu[:150] + "..." if len(self.contenu) > 150 else self.contenu

class Newsletter(models.Model):
    """Campagne d'email envoyée à une liste d'abonnés."""

    STATUTS = [
        ('brouillon', 'Brouillon'),
        ('envoyee', 'Envoyée'),
        ('programmee', 'Programmée'),
    ]

    sujet = models.CharField(max_length=200)
    contenu = models.TextField()
    piece_jointe = models.FileField(upload_to='newsletter/files/', blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_envoi = models.DateTimeField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='brouillon')
    cible = models.CharField(max_length=200, blank=True, null=True, help_text="Ex : tous, clients, abonnés actifs, etc.")
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Newsletter"
        verbose_name_plural = "Newsletters"

    def __str__(self):
        return f"{self.sujet} ({self.get_statut_display()})"

    # ✅ Déterminer si la newsletter a été envoyée
    def est_envoyee(self):
        return self.statut == 'envoyee'

    # ✅ Programmation automatique
    def programmer_envoi(self, date_envoi):
        self.statut = 'programmee'
        self.date_envoi = date_envoi
        self.save(update_fields=['statut', 'date_envoi'])

class Subscriber(models.Model):
    """Abonné à la newsletter."""

    email = models.EmailField(unique=True)
    nom = models.CharField(max_length=100, blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True, help_text="Origine de l’inscription (site, campagne, etc.)")
    date_inscription = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    derniere_newsletter = models.ForeignKey(
        Newsletter,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='abonnes_contactes'
    )

    class Meta:
        ordering = ['-date_inscription']
        verbose_name = "Abonné"
        verbose_name_plural = "Abonnés"

    def __str__(self):
        return f"{self.email} {'(inactif)' if not self.actif else ''}"

    # ✅ Se désinscrire proprement
    def desinscrire(self):
        self.actif = False
        self.save(update_fields=['actif'])

    # ✅ Retourne la durée depuis l’inscription
    def anciennete(self):
        delta = timezone.now() - self.date_inscription
        return f"{delta.days} jours"

    # ✅ Vérifie si un abonné a déjà reçu une newsletter spécifique
    def a_recu(self, newsletter):
        return self.derniere_newsletter == newsletter

        
class Notification(models.Model):
    """Notification envoyée à un utilisateur (système ou marketing)."""

    TYPES = [
        ('info', 'Information'),
        ('alerte', 'Alerte'),
        ('message', 'Message direct'),
        ('systeme', 'Système'),
        ('marketing', 'Marketing'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=TYPES, default='info')
    titre = models.CharField(max_length=200)
    message = models.TextField()
    url_action = models.URLField(blank=True, null=True, help_text="Lien de redirection si applicable")
    lu = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(auto_now_add=True)
    date_lecture = models.DateTimeField(blank=True, null=True)
    priorite = models.CharField(max_length=20, default='normale', choices=[
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
    ])

    class Meta:
        ordering = ['-date_envoi']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.titre} ({self.get_type_display()})"

    # ✅ Marquer la notification comme lue
    def marquer_comme_lue(self):
        self.lu = True
        self.date_lecture = timezone.now()
        self.save(update_fields=['lu', 'date_lecture'])

    # ✅ Temps écoulé depuis l’envoi
    def temps_ecoule(self):
        delta = timezone.now() - self.date_envoi
        heures = delta.seconds // 3600
        if delta.days > 0:
            return f"{delta.days} j {heures} h"
        return f"{heures} h"

    # ✅ Code couleur pour affichage
    def type_badge(self):
        colors = {
            'info': 'primary',
            'alerte': 'danger',
            'message': 'success',
            'systeme': 'secondary',
            'marketing': 'warning',
        }
        return colors.get(self.type, 'light')
