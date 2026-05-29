from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class SupportTicket(models.Model):
    """Ticket d’assistance créé par un utilisateur (client ou employé)."""

    STATUTS = [
        ('ouvert', 'Ouvert'),
        ('en_cours', 'En cours de traitement'),
        ('attente_client', 'En attente du client'),
        ('resolu', 'Résolu'),
        ('ferme', 'Fermé'),
    ]

    PRIORITES = [
        ('basse', 'Basse'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]

    id_public = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    sujet = models.CharField(max_length=200)
    message = models.TextField()
    statut = models.CharField(max_length=20, choices=STATUTS, default='ouvert')
    priorite = models.CharField(max_length=20, choices=PRIORITES, default='moyenne')
    assigné_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets_assignes',
        help_text="Employé responsable du suivi"
    )
    categorie = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Ex: Facturation, Technique, Support Client..."
    )
    reference = models.CharField(max_length=50, unique=True, editable=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    date_resolution = models.DateTimeField(blank=True, null=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Ticket d'assistance"
        verbose_name_plural = "Tickets d'assistance"

    def __str__(self):
        return f"{self.reference} - {self.sujet}"

    # ✅ Génération automatique d’une référence lisible
    def save(self, *args, **kwargs):
        if not self.reference:
            date_part = timezone.now().strftime("%Y%m%d")
            count = SupportTicket.objects.filter(date_creation__date=timezone.now().date()).count() + 1
            self.reference = f"TCK-{date_part}-{count:04d}"
        super().save(*args, **kwargs)

    # ✅ Temps écoulé depuis la création
    def duree_ouverte(self):
        delta = timezone.now() - self.date_creation
        jours, heures = delta.days, delta.seconds // 3600
        if jours > 0:
            return f"{jours} j {heures} h"
        return f"{heures} h"

    # ✅ Déterminer si le ticket est en attente d’une réponse client
    def en_attente_client(self):
        return self.statut == 'attente_client'

    # ✅ Marquer comme résolu
    def marquer_resolu(self):
        self.statut = 'resolu'
        self.date_resolution = timezone.now()
        self.save(update_fields=['statut', 'date_resolution'])

    # ✅ Code couleur (utile pour front ou admin)
    def statut_badge(self):
        colors = {
            'ouvert': 'primary',
            'en_cours': 'info',
            'attente_client': 'warning',
            'resolu': 'success',
            'ferme': 'secondary',
        }
        return colors.get(self.statut, 'light')

    # ✅ Temps de réponse estimé selon la priorité
    def delai_theorique(self):
        delais = {
            'basse': 72,
            'moyenne': 48,
            'haute': 24,
            'critique': 6,
        }
        heures = delais.get(self.priorite, 48)
        return f"{heures} heures"

class TicketMessage(models.Model):
    """Messages échangés entre le client et le support dans un ticket."""

    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenu = models.TextField()
    piece_jointe = models.FileField(upload_to='support/files/', blank=True, null=True)
    visible_par_client = models.BooleanField(default=True, help_text="Permet de masquer un message interne")
    date_message = models.DateTimeField(auto_now_add=True)
    modifie = models.BooleanField(default=False)
    date_modification = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['date_message']
        verbose_name = "Message de ticket"
        verbose_name_plural = "Messages de ticket"

    def __str__(self):
        return f"Message de {self.auteur.username} ({self.date_message.strftime('%d/%m %H:%M')})"

    # ✅ Marquer un message comme modifié
    def modifier_message(self, nouveau_contenu):
        self.contenu = nouveau_contenu
        self.modifie = True
        self.date_modification = timezone.now()
        self.save(update_fields=['contenu', 'modifie', 'date_modification'])

    # ✅ Indique si le message provient du staff ou du client
    def est_staff(self):
        return self.auteur.role in ['admin', 'employe']

    # ✅ Raccourci pour affichage front (extrait)
    def resume(self):
        return self.contenu[:50] + ('...' if len(self.contenu) > 50 else '')
