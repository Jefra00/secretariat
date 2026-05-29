from django.contrib import admin
from django.utils.html import format_html
from .models import BlogPost, Newsletter, Subscriber, Notification


# ✅ BLOG
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        'titre', 'auteur', 'categorie', 'statut_colore',
        'date_publication', 'vues', 'en_avant'
    )
    list_filter = ('statut', 'categorie', 'en_avant', 'date_publication')
    search_fields = ('titre', 'contenu', 'categorie', 'auteur__username')
    # ❌ On supprime cette ligne :
    # prepopulated_fields = {"slug": ("titre",)}
    readonly_fields = ('slug', 'date_creation', 'date_modification', 'date_publication', 'vues')
    ordering = ('-date_publication',)
    list_editable = ('en_avant',)

    fieldsets = (
        ('📰 Informations principales', {
            'fields': ('titre', 'auteur', 'categorie', 'image_couverture')
        }),
        ('🖋️ Contenu', {
            'fields': ('contenu',)
        }),
        ('⚙️ Statut & Publication', {
            'fields': ('statut', 'en_avant', 'date_publication')
        }),
        ('📆 Dates et vues', {
            'fields': ('slug', 'date_creation', 'date_modification', 'vues'),
            'classes': ('collapse',)
        }),
    )

    def statut_colore(self, obj):
        couleurs = {
            'publie': 'green',
            'brouillon': 'gray',
            'archive': 'orange'
        }
        color = couleurs.get(obj.statut, 'black')
        return format_html(f'<b style="color:{color}">{obj.get_statut_display()}</b>')
    statut_colore.short_description = "Statut"

    @admin.action(description="🟢 Publier les articles sélectionnés")
    def publier(self, request, queryset):
        updated = queryset.update(statut='publie', date_publication=None)
        self.message_user(request, f"{updated} article(s) publiés avec succès.")
    actions = ['publier']


# ✅ NEWSLETTER
@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('sujet', 'statut', 'date_creation', 'date_envoi', 'cible', 'auteur')
    list_filter = ('statut', 'date_creation', 'date_envoi')
    search_fields = ('sujet', 'contenu', 'cible')
    readonly_fields = ('date_creation',)
    ordering = ('-date_creation',)

    fieldsets = (
        ('✉️ Informations principales', {
            'fields': ('sujet', 'contenu', 'piece_jointe')
        }),
        ('⚙️ Envoi', {
            'fields': ('statut', 'cible', 'date_envoi', 'auteur')
        }),
        ('📅 Dates', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )


# ✅ SUBSCRIBER (Abonnés)
@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'nom', 'actif', 'date_inscription', 'source', 'derniere_newsletter')
    list_filter = ('actif', 'source', 'date_inscription')
    search_fields = ('email', 'nom')
    ordering = ('-date_inscription',)
    actions = ['activer_abonnes', 'desactiver_abonnes']

    @admin.action(description="✅ Activer les abonnés sélectionnés")
    def activer_abonnes(self, request, queryset):
        updated = queryset.update(actif=True)
        self.message_user(request, f"{updated} abonné(s) activé(s).")

    @admin.action(description="🚫 Désactiver les abonnés sélectionnés")
    def desactiver_abonnes(self, request, queryset):
        updated = queryset.update(actif=False)
        self.message_user(request, f"{updated} abonné(s) désactivé(s).")


# ✅ NOTIFICATIONS
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'user', 'type_badge_colore', 'priorite', 'lu', 'date_envoi')
    list_filter = ('type', 'priorite', 'lu', 'date_envoi')
    search_fields = ('titre', 'message', 'user__username')
    readonly_fields = ('date_envoi', 'date_lecture')
    ordering = ('-date_envoi',)

    def type_badge_colore(self, obj):
        couleurs = {
            'info': 'blue', 'alerte': 'red', 'message': 'green',
            'systeme': 'gray', 'marketing': 'orange'
        }
        color = couleurs.get(obj.type, 'black')
        return format_html(f'<b style="color:{color}">{obj.get_type_display()}</b>')
    type_badge_colore.short_description = "Type"
