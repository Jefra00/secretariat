from django.db import models
from django.utils import timezone
from services.models import Service
import uuid


class Company(models.Model):
    """Entreprise cliente utilisant la plateforme."""

    id_public = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    nom = models.CharField(max_length=200)
    secteur = models.CharField(max_length=150)
    email_contact = models.EmailField()
    telephone = models.CharField(max_length=20)
    adresse = models.TextField(blank=True, null=True)
    site_web = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='companies/logos/', blank=True, null=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    note_globale = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    nombre_commandes = models.PositiveIntegerField(default=0)
    commentaire_interne = models.TextField(blank=True, null=True, help_text="Notes internes non visibles par l'entreprise")

    class Meta:
        ordering = ['nom']
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"

    def __str__(self):
        return self.nom

    # ✅ Nombre de services personnalisés
    def nombre_services(self):
        return self.services_personnalises.count()

    # ✅ Calcul automatique du score moyen
    def update_note_globale(self, nouvelle_note):
        if self.note_globale == 0:
            self.note_globale = nouvelle_note
        else:
            self.note_globale = round((self.note_globale + nouvelle_note) / 2, 2)
        self.save(update_fields=['note_globale'])

    # ✅ Statut d’activité
    def statut(self):
        return "Active" if self.actif else "Suspendue"

    # ✅ Durée depuis inscription
    def anciennete(self):
        delta = timezone.now() - self.date_inscription
        return f"{delta.days} jours"

    # ✅ Formate un affichage propre des coordonnées
    def coordonnees(self):
        return f"{self.email_contact} | {self.telephone}"

    # ✅ Mise à jour automatique du nombre de commandes
    def incrementer_commandes(self):
        self.nombre_commandes += 1
        self.save(update_fields=['nombre_commandes'])


class CompanyService(models.Model):
    """Service personnalisé attribué à une entreprise."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='services_personnalises')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='entreprises_associees')
    forfait = models.CharField(max_length=100, blank=True, null=True, help_text="Nom du pack ou du plan tarifaire")
    tarif_personnalise = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description_forfait = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    renouvellement_auto = models.BooleanField(default=False)
    date_renouvellement = models.DateField(blank=True, null=True)
    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('company', 'service')
        ordering = ['-date_creation']
        verbose_name = "Service personnalisé d'entreprise"
        verbose_name_plural = "Services personnalisés d'entreprises"

    def __str__(self):
        return f"{self.company.nom} → {self.service.nom}"

    # ✅ Calcul du tarif final (utilise celui du service par défaut si non défini)
    def tarif_final(self):
        return self.tarif_personnalise or self.service.prix_base

    # ✅ Vérifie si le service est actif et à jour
    def est_actif(self):
        if not self.actif:
            return False
        if self.date_renouvellement and self.date_renouvellement < timezone.now().date():
            return False
        return True

    # ✅ Active/désactive le renouvellement automatique
    def basculer_renouvellement(self):
        self.renouvellement_auto = not self.renouvellement_auto
        self.save(update_fields=['renouvellement_auto'])

    # ✅ Mise à jour du tarif personnalisé
    def update_tarif(self, nouveau_tarif):
        self.tarif_personnalise = nouveau_tarif
        self.save(update_fields=['tarif_personnalise'])