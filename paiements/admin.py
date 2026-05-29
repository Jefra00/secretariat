from django.contrib import admin
from .models import Payment, Invoice

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reference_transaction', 'order', 'mode', 'montant', 'devise', 'statut', 'date_paiement', 'date_validation')
    list_filter = ('statut', 'mode', 'devise')
    search_fields = ('reference_transaction', 'order__code_commande', 'order__client__username')
    readonly_fields = ('reference_transaction', 'id_transaction', 'date_paiement', 'date_validation')
    autocomplete_fields = ['order']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('numero_facture', 'payment', 'montant_total', 'tva', 'montant_ttc', 'valide', 'date_emission')
    list_filter = ('valide',)
    search_fields = ('numero_facture', 'payment__reference_transaction')
    readonly_fields = ('numero_facture', 'date_emission', 'date_modification', 'montant_ttc')
