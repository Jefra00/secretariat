from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class ActivityLog(models.Model):
    """Journal d’activité des utilisateurs pour audit et sécurité."""

    CATEGORIES = [
        ('connexion', 'Connexion'),
        ('deconnexion', 'Déconnexion'),
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
        ('consultation', 'Consultation'),
        ('telechargement', 'Téléchargement'),
        ('systeme', 'Système'),
        ('autre', 'Autre'),
    ]

    id_public = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs_activite'
    )
    categorie = models.CharField(max_length=50, choices=CATEGORIES, default='autre')
    action = models.CharField(max_length=200, help_text="Description courte de l’action effectuée")
    description = models.TextField(blank=True, null=True, help_text="Détails supplémentaires sur l’action")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True, help_text="Navigateur / client utilisé")
    date_action = models.DateTimeField(auto_now_add=True)
    succes = models.BooleanField(default=True, help_text="Indique si l’action s’est déroulée sans erreur")
    objet_concerne = models.CharField(max_length=255, blank=True, null=True, help_text="Nom de l’objet ou ressource ciblée")

    class Meta:
        ordering = ['-date_action']
        verbose_name = "Journal d'activité"
        verbose_name_plural = "Journaux d'activité"
        indexes = [
            models.Index(fields=['categorie']),
            models.Index(fields=['user']),
            models.Index(fields=['date_action']),
        ]

    def __str__(self):
        utilisateur = self.user.username if self.user else "Système"
        return f"{utilisateur} - {self.action} ({self.categorie})"

    # ✅ Récupère la durée depuis l’action
    def temps_ecoule(self):
        delta = timezone.now() - self.date_action
        heures = delta.seconds // 3600
        if delta.days > 0:
            return f"{delta.days} j {heures} h"
        return f"{heures} h"

    # ✅ Retourne une icône contextuelle pour le front
    def icone_categorie(self):
        icones = {
            'connexion': 'fa-sign-in-alt',
            'deconnexion': 'fa-sign-out-alt',
            'creation': 'fa-plus-circle',
            'modification': 'fa-edit',
            'suppression': 'fa-trash-alt',
            'consultation': 'fa-eye',
            'telechargement': 'fa-download',
            'systeme': 'fa-cog',
            'autre': 'fa-info-circle',
        }
        return icones.get(self.categorie, 'fa-info-circle')

    # ✅ Génération d’un résumé compact
    def resume(self):
        return f"[{self.categorie.upper()}] {self.action[:60]}"

    # ✅ Méthode statique pour enregistrer facilement un log depuis le code
    @staticmethod
    def enregistrer(user, categorie, action, description="", ip=None, user_agent=None, succes=True, objet=None):
        """Crée rapidement une entrée dans le journal d'activité."""
        return ActivityLog.objects.create(
            user=user,
            categorie=categorie,
            action=action,
            description=description,
            ip_address=ip,
            user_agent=user_agent,
            succes=succes,
            objet_concerne=objet
        )
