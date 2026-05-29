from django.db import models
from django.conf import settings
from django.utils import timezone
from services.models import Service
from django.utils.text import slugify


class Order(models.Model):
    """Modèle de gestion des commandes client pour les services proposés."""

    STATUTS = [
        ('en_attente_paiement', 'En attente de paiement'),
        ('en_attente', 'En attente de traitement'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ]


    MODES_PAIEMENT = [
        ('mobile_money', 'Mobile Money'),
        ('carte', 'Carte bancaire'),
        ('virement', 'Virement bancaire'),
        ('autre', 'Autre'),
    ]

    code_commande = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Code unique généré automatiquement"
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='commandes'
    )
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    remise_appliquee = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Remise en % appliquée sur la commande")
    mode_paiement = models.CharField(max_length=50, choices=MODES_PAIEMENT, blank=True, null=True)
    notes_client = models.TextField(blank=True, null=True, help_text="Commentaires ou précisions du client")
    notes_interne = models.TextField(blank=True, null=True, help_text="Notes internes visibles par l'équipe uniquement")

    date_commande = models.DateTimeField(auto_now_add=True)
    date_livraison = models.DateTimeField(blank=True, null=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    resultats = models.ManyToManyField(
        'OrderFile',
        related_name='commandes_resultats',
        blank=True,
        help_text="Fichiers livrés au client (résultats finaux)"
    )

    class Meta:
        ordering = ['-date_commande']
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"

    def __str__(self):
        return f"{self.code_commande} - {self.client.get_full_name() or self.client.username}"

    # ✅ Génération automatique du code commande (ex: CMD-2025-00045)
    def save(self, *args, **kwargs):
        if not self.code_commande:
            date_part = timezone.now().strftime("%Y%m%d")
            prefix = "CMD"
            last_order = Order.objects.order_by('id').last()
            next_id = last_order.id + 1 if last_order else 1
            self.code_commande = f"{prefix}-{date_part}-{next_id:05d}"
        super().save(*args, **kwargs)

    # ✅ Prix final après remise
    def montant_final(self):
        return round(self.montant_total * (1 - (self.remise_appliquee / 100)), 2)

    # ✅ Temps restant estimé avant la livraison
    def temps_restant(self):
        if self.date_livraison:
            delta = self.date_livraison - timezone.now()
            jours = delta.days
            if jours > 0:
                return f"{jours} jours restants"
            elif jours == 0:
                return "Livraison aujourd’hui"
            else:
                return f"Retard de {-jours} jours"
        return "Date de livraison non définie"

    # ✅ Détermine si la commande est en retard
    def est_en_retard(self):
        return self.date_livraison and timezone.now() > self.date_livraison and self.statut != 'termine'

    # ✅ Permet de changer facilement le statut (workflow interne)
    def changer_statut(self, nouveau_statut):
        self.statut = nouveau_statut
        self.save(update_fields=['statut', 'date_modification'])
        return self.statut

    # ✅ Utilisé pour afficher un badge dans le front ou admin
    def statut_badge(self):
        colors = {
            'en_attente': 'warning',
            'en_cours': 'info',
            'termine': 'success',
            'annule': 'danger'
        }
        return colors.get(self.statut, 'secondary')
    
    


class OrderFile(models.Model):
    """Fichiers liés à une commande (pièces, livrables, justificatifs, etc.)"""

    TYPE_FICHIER = [
        ('document_client', 'Document client'),
        ('livrable', 'Livrable final'),
        ('autre', 'Autre'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='fichiers')
    fichier = models.FileField(upload_to='commandes/')
    type_fichier = models.CharField(max_length=50, choices=TYPE_FICHIER, default='autre')
    nom_original = models.CharField(max_length=255, blank=True, null=True)
    commentaire = models.TextField(blank=True, null=True)
    date_upload = models.DateTimeField(auto_now_add=True)
    taille = models.PositiveIntegerField(blank=True, null=True, help_text="Taille du fichier en octets")

    class Meta:
        ordering = ['-date_upload']
        verbose_name = "Fichier de commande"
        verbose_name_plural = "Fichiers de commande"

    def __str__(self):
        return f"{self.type_fichier} - {self.fichier.name}"

    # ✅ Calcul automatique de la taille du fichier
    def save(self, *args, **kwargs):
        if self.fichier and not self.taille:
            try:
                self.taille = self.fichier.size
                self.nom_original = self.fichier.name
            except Exception:
                pass
        super().save(*args, **kwargs)

    # ✅ Retourne la taille formatée (lisible)
    def taille_formattee(self):
        if not self.taille:
            return "0 Ko"
        if self.taille < 1024:
            return f"{self.taille} o"
        elif self.taille < 1024**2:
            return f"{self.taille / 1024:.1f} Ko"
        else:
            return f"{self.taille / (1024**2):.1f} Mo"

class ResultFile(models.Model):
    """
    Fichier livré au client une fois la commande terminée.
    """
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="resultat")
    nom = models.CharField(max_length=255, blank=True, null=True, help_text="Nom lisible du fichier livré")
    fichier = models.FileField(upload_to="resultats_commandes/")
    commentaire = models.TextField(blank=True, null=True, help_text="Détails ou explications du travail effectué")
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fichier résultat"
        verbose_name_plural = "Fichiers résultats"
        ordering = ["-date_ajout"]

    def __str__(self):
        return self.nom or f"Résultat #{self.id} pour {self.order.code_commande}"
