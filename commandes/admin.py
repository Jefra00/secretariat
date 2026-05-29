from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderFile, ResultFile


# ==========================
# INLINE : Fichiers clients liés à une commande
# ==========================
class OrderFileInline(admin.TabularInline):
    model = OrderFile
    extra = 1
    fields = ('fichier', 'type_fichier', 'nom_original', 'taille_formattee', 'commentaire', 'date_upload')
    readonly_fields = ('nom_original', 'taille_formattee', 'date_upload')
    verbose_name = "Fichier client"
    verbose_name_plural = "Fichiers clients associés"

    def taille_formattee(self, obj):
        return obj.taille_formattee()
    taille_formattee.short_description = "Taille"


# ==========================
# INLINE : Fichiers livrés (résultats)
# ==========================
class ResultFileInline(admin.TabularInline):
    model = ResultFile
    extra = 1
    fields = ('nom', 'fichier', 'commentaire', 'date_ajout')
    readonly_fields = ('date_ajout',)
    verbose_name = "Fichier livrable"
    verbose_name_plural = "Fichiers livrés au client"


# ==========================
# ADMIN : Commandes
# ==========================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'code_commande',
        'client',
        'service',
        'statut_colore',
        'montant_final_affiche',
        'mode_paiement',
        'date_commande',
        'date_livraison',
        'est_en_retard_colore',
    )
    list_filter = ('statut', 'mode_paiement', 'actif', 'date_commande', 'service__category')
    search_fields = ('code_commande', 'client__username', 'client__first_name', 'client__last_name', 'service__nom')
    ordering = ('-date_commande',)
    
    # ✅ On ajoute les deux inlines ici
    inlines = [OrderFileInline, ResultFileInline]

    readonly_fields = ('code_commande', 'date_commande', 'date_modification')
    fieldsets = (
        ("Informations client", {
            'fields': ('client', 'adresse')
        }),
        ("Détails de la commande", {
            'fields': ('service', 'statut', 'mode_paiement', 'montant_total', 'remise_appliquee')
        }),
        ("Dates", {
            'fields': ('date_commande', 'date_livraison', 'date_modification'),
            'classes': ('collapse',)
        }),
        ("Notes & suivi", {
            'fields': ('notes_client', 'notes_interne')
        }),
        ("Système", {
            'fields': ('code_commande', 'actif'),
            'classes': ('collapse',)
        }),
    )

    # ==== Champs joliment affichés ====
    def statut_colore(self, obj):
        couleurs = {
            'en_attente': '#f59e0b',   # orange
            'en_cours': '#3b82f6',     # bleu
            'termine': '#16a34a',      # vert
            'annule': '#dc2626',       # rouge
        }
        couleur = couleurs.get(obj.statut, '#6b7280')
        return format_html(
            '<span style="background-color:{};color:white;padding:2px 8px;border-radius:6px;font-size:12px;">{}</span>',
            couleur,
            obj.get_statut_display()
        )
    statut_colore.short_description = "Statut"

    def est_en_retard_colore(self, obj):
        if obj.est_en_retard():
            return format_html('<span style="color:#dc2626;font-weight:bold;">⚠️ En retard</span>')
        return format_html('<span style="color:#16a34a;">✔️ À temps</span>')
    est_en_retard_colore.short_description = "État"

    def montant_final_affiche(self, obj):
        try:
            return f"{obj.montant_final():,.2f} €"
        except Exception:
            return "—"
    montant_final_affiche.short_description = "Montant final"

    class Media:
        css = {
            'all': ('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap',)
        }


# ==========================
# ADMIN : Fichiers résultats (accès direct)
# ==========================
@admin.register(ResultFile)
class ResultFileAdmin(admin.ModelAdmin):
    list_display = ("order", "nom", "date_ajout")
    search_fields = ("order__code_commande", "nom")
    list_filter = ("date_ajout",)
