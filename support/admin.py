from django.contrib import admin
from .models import SupportTicket, TicketMessage


# 🔹 Inline pour afficher les messages à l’intérieur d’un ticket
class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    fields = ('auteur', 'contenu', 'piece_jointe', 'visible_par_client', 'date_message')
    readonly_fields = ('date_message',)
    show_change_link = True
    ordering = ('-date_message',)


# 🔹 Admin principal pour SupportTicket
@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        'reference', 'sujet', 'user', 'statut', 'priorite', 
        'assigné_a', 'categorie', 'date_creation', 'actif'
    )
    list_filter = (
        'statut', 'priorite', 'categorie', 'actif', 
        ('date_creation', admin.DateFieldListFilter),
    )
    search_fields = (
        'reference', 'sujet', 'message', 
        'user__username', 'assigné_a__username'
    )
    ordering = ('-date_creation',)
    readonly_fields = ('reference', 'date_creation', 'date_mise_a_jour', 'date_resolution')
    inlines = [TicketMessageInline]

    fieldsets = (
        ('📋 Informations principales', {
            'fields': ('reference', 'user', 'sujet', 'message', 'categorie')
        }),
        ('⚙️ Détails du ticket', {
            'fields': ('statut', 'priorite', 'assigné_a', 'actif')
        }),
        ('⏱️ Dates', {
            'fields': ('date_creation', 'date_mise_a_jour', 'date_resolution'),
            'classes': ('collapse',)
        }),
    )

    # 🔸 Couleur et badge dans la liste
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'assigné_a')

    def statut_colore(self, obj):
        couleurs = {
            'ouvert': 'background:#2563eb;color:white;',
            'en_cours': 'background:#0284c7;color:white;',
            'attente_client': 'background:#f59e0b;color:white;',
            'resolu': 'background:#10b981;color:white;',
            'ferme': 'background:#6b7280;color:white;',
        }
        style = couleurs.get(obj.statut, 'background:#ccc;color:black;')
        return f'<span style="padding:3px 8px;border-radius:4px;{style}">{obj.get_statut_display()}</span>'
    statut_colore.allow_tags = True
    statut_colore.short_description = "Statut"


# 🔹 Admin pour TicketMessage (accès direct si besoin)
@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'auteur', 'resume', 'date_message', 'visible_par_client', 'modifie')
    list_filter = ('visible_par_client', 'modifie', 'date_message')
    search_fields = ('contenu', 'ticket__reference', 'auteur__username')
    readonly_fields = ('date_message', 'date_modification')
    ordering = ('-date_message',)

    fieldsets = (
        ('💬 Message', {
            'fields': ('ticket', 'auteur', 'contenu', 'piece_jointe')
        }),
        ('⚙️ Détails', {
            'fields': ('visible_par_client', 'modifie', 'date_message', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
