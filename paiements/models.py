from django.db import models
from django.utils import timezone
from decimal import Decimal
from commandes.models import Order
import uuid


class Payment(models.Model):
    """Gestion des paiements effectués pour une commande."""

    STATUTS = [
        ('en_attente', 'En attente de validation'),
        ('valide', 'Validé'),
        ('echoue', 'Échoué'),
        ('rembourse', 'Remboursé'),
    ]

    MODES = [
        ('mobile_money', 'Mobile Money'),
        ('carte', 'Carte bancaire'),
        ('virement', 'Virement bancaire'),
        ('espece', 'Espèces'),
    ]

    id_transaction = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=10, default='XAF', help_text="Devise du paiement")
    mode = models.CharField(max_length=30, choices=MODES)
    reference_transaction = models.CharField(max_length=100, unique=True, editable=False)
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    commentaire = models.TextField(blank=True, null=True, help_text="Informations supplémentaires sur la transaction")
    date_paiement = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(blank=True, null=True)
    date_modification = models.DateTimeField(auto_now=True)
    recu_url = models.URLField(blank=True, null=True, help_text="Lien vers le reçu de paiement (si disponible)")

    class Meta:
        ordering = ['-date_paiement']
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"{self.reference_transaction} ({self.get_statut_display()})"

    # ✅ Génère automatiquement une référence lisible
    def save(self, *args, **kwargs):
        if not self.reference_transaction:
            prefix = "PAY"
            date_part = timezone.now().strftime("%Y%m%d")
            count = Payment.objects.filter(date_paiement__date=timezone.now().date()).count() + 1
            self.reference_transaction = f"{prefix}-{date_part}-{count:04d}"
        super().save(*args, **kwargs)

    # ✅ Validation automatique du paiement
    def valider(self):
        self.statut = 'valide'
        self.date_validation = timezone.now()
        self.save(update_fields=['statut', 'date_validation'])
        # Génération automatique de la facture
        Invoice.objects.create(
            payment=self,
            montant_total=self.montant,
            tva=Decimal("19.25")
        )

    # ✅ Vérifie si complet
    def est_complet(self):
        total_paye = sum(p.montant for p in self.order.paiements.filter(statut='valide'))
        return total_paye >= self.order.montant_total

    # ✅ Reste à payer
    def montant_restant(self):
        total_paye = sum(p.montant for p in self.order.paiements.filter(statut='valide'))
        return max(0, self.order.montant_total - total_paye)


class Invoice(models.Model):
    """Facture générée à partir d’un paiement validé."""

    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='facture')
    numero_facture = models.CharField(max_length=50, unique=True, editable=False)
    pdf_url = models.URLField(blank=True, null=True, help_text="Lien vers le fichier PDF de la facture")
    date_emission = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, help_text="Montant total facturé")
    tva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), help_text="TVA en pourcentage")
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    signature_admin = models.CharField(max_length=255, blank=True, null=True)
    valide = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date_emission']
        verbose_name = "Facture"
        verbose_name_plural = "Factures"

    def __str__(self):
        return f"Facture {self.numero_facture}"

    def save(self, *args, **kwargs):
        # ✅ Numéro unique
        if not self.numero_facture:
            prefix = "INV"
            date_part = timezone.now().strftime("%Y%m%d")
            count = Invoice.objects.filter(date_emission__date=timezone.now().date()).count() + 1
            self.numero_facture = f"{prefix}-{date_part}-{count:04d}"

        # ✅ Calcul correct du TTC
        montant_total_decimal = Decimal(str(self.montant_total))
        tva_decimal = Decimal(str(self.tva)) / Decimal("100")
        self.montant_ttc = montant_total_decimal * (Decimal("1") + tva_decimal)

        super().save(*args, **kwargs)

    def montant_ttc_formatte(self):
        devise = getattr(self.payment, "devise", "")
        return f"{self.montant_ttc:,.2f} {devise}"

    def commande_associee(self):
        return self.payment.order

    def statut_facture(self):
        return "Active" if self.valide else "Annulée"

    def save(self, *args, **kwargs):
        if not self.numero_facture:
            prefix = "INV"
            date_part = timezone.now().strftime("%Y%m%d")
            count = Invoice.objects.filter(date_emission__date=timezone.now().date()).count() + 1
            self.numero_facture = f"{prefix}-{date_part}-{count:04d}"

        tva_decimal = Decimal(self.tva) / Decimal(100)
        self.montant_ttc = self.montant_total * (Decimal(1) + tva_decimal)

        super().save(*args, **kwargs)

    # 💾 Exemple de lien PDF fictif si tu n’as pas encore de génération automatique
        if not self.pdf_url:
            self.pdf_url = f"/media/factures/{self.numero_facture}.pdf"
            super().save(update_fields=["pdf_url"])

