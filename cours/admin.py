from django.contrib import admin, messages
from django.utils.html import format_html
from django.db import models
from django_json_widget.widgets import JSONEditorWidget
from django.utils import timezone
from .models import (
    Course, Chapter, Lesson, KnowledgeCheck,
    CourseEnrollment, CourseSession, ChapterProgress
)
import openai
import os


# ===========================
# 🔹 CONFIGURATION OPENAI
# ===========================
openai.api_key = os.getenv("OPENAI_API_KEY")


# ===========================
# 🔹 INLINE ADMIN
# ===========================
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('ordre', 'titre', 'video_url', 'duree_video', 'generer_retro_ai_button', 'retro_ai')
    readonly_fields = ('generer_retro_ai_button',)

    def generer_retro_ai_button(self, obj):
        if not obj.id:
            return "💾 Enregistrez la leçon d’abord."
        return format_html(
            '<a class="button" href="/admin/training/lesson/{}/generate_retro_ai/" '
            'style="padding:6px 12px; background:#197fe6; color:white; border-radius:5px; text-decoration:none;">'
            '🧠 Générer rétro IA</a>', obj.id
        )
    generer_retro_ai_button.short_description = "Rétroaction IA"


class KnowledgeCheckInline(admin.TabularInline):
    model = KnowledgeCheck
    extra = 1
    fields = ('question', 'bonne_reponse', 'feedback')


class ChapterInline(admin.StackedInline):
    model = Chapter
    extra = 1
    fields = ('ordre', 'titre', 'controle_obligatoire')
    show_change_link = True
    inlines = [LessonInline, KnowledgeCheckInline]


# ===========================
# 🎓 ADMIN DU COURS
# ===========================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'titre', 'niveau', 'mode', 'prix', 'actif',
        'afficher_statut', 'date_creation', 'resume_ai_preview'
    )
    list_filter = ('mode', 'niveau', 'actif')
    search_fields = ('titre', 'description')
    list_editable = ('actif',)
    ordering = ('-date_creation',)
    readonly_fields = ('id_public', 'date_creation', 'date_modification', 'nombre_participants', 'presentation_ai')
    inlines = [ChapterInline]

    fieldsets = (
        ('Informations générales', {
            'fields': (
                'id_public', 'titre', 'description', 'niveau',
                'mode', 'prix', 'duree', 'image_couverture', 'presentation_ai'
            )
        }),
        ('Configuration avancée', {
            'fields': ('actif', 'certificat_disponible', 'date_creation', 'date_modification')
        }),
    )

    actions = ['generer_resume_ia_action']

    def afficher_statut(self, obj):
        color = "green" if obj.actif else "gray"
        return format_html(f"<b style='color:{color}'>{obj.statut()}</b>")
    afficher_statut.short_description = "Statut"

    def resume_ai_preview(self, obj):
        """Aperçu court du résumé IA"""
        if obj.presentation_ai:
            return obj.presentation_ai[:80] + "..."
        return format_html("<span style='color:gray;'>Non généré</span>")
    resume_ai_preview.short_description = "Résumé IA"

    @admin.action(description="🧠 Générer un résumé IA pour les cours sélectionnés")
    def generer_resume_ia_action(self, request, queryset):
        """Action en masse pour générer un résumé IA via OpenAI"""
        for course in queryset:
            try:
                prompt = f"Résume de manière concise le cours suivant : {course.titre}. Description : {course.description}"
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Tu es un assistant qui résume des cours de formation."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6
                )
                resume = response.choices[0].message.content.strip()
                course.presentation_ai = resume
                course.date_modification = timezone.now()
                course.save()
            except Exception as e:
                messages.error(request, f"Erreur IA pour {course.titre} : {e}")
        messages.success(request, "✅ Résumés IA générés avec succès !")


# ===========================
# 🧩 CHAPITRES
# ===========================
@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('titre', 'course', 'ordre', 'controle_obligatoire', 'nb_lecons', 'nb_quiz')
    inlines = [LessonInline, KnowledgeCheckInline]
    ordering = ('course', 'ordre')

    def nb_lecons(self, obj):
        return obj.lecons.count()
    nb_lecons.short_description = "Leçons"

    def nb_quiz(self, obj):
        return obj.quiz.count()
    nb_quiz.short_description = "Quiz"


# ===========================
# 🎬 LEÇONS
# ===========================
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('titre', 'chapitre', 'ordre', 'duree_video', 'retro_tag')
    list_filter = ('chapitre__course',)
    search_fields = ('titre', 'description', 'retro_ai')
    ordering = ('chapitre', 'ordre')

    def retro_tag(self, obj):
        if obj.retro_ai:
            return format_html('<span style="color:green;">✅ Générée</span>')
        return format_html('<span style="color:gray;">❌ Non générée</span>')
    retro_tag.short_description = "Rétro IA"


# ===========================
# 🧠 CONTRÔLES DE CONNAISSANCE
# ===========================
@admin.register(KnowledgeCheck)
class KnowledgeCheckAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
    list_display = ('chapitre', 'question', 'bonne_reponse')
    search_fields = ('question', 'chapitre__titre')


# ===========================
# 🎯 SESSIONS
# ===========================
@admin.register(CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    list_display = ('course', 'formateur', 'date_debut', 'date_fin', 'lieu', 'capacite_max', 'inscrits', 'taux_occupation_color', 'statut')
    readonly_fields = ('inscrits',)

    def taux_occupation_color(self, obj):
        taux = obj.taux_occupation()
        color = "green" if taux >= 80 else "orange" if taux >= 50 else "gray"
        return format_html(f"<b style='color:{color}'>{taux}%</b>")
    taux_occupation_color.short_description = "Taux d’occupation"


# ===========================
# 👨‍🎓 INSCRIPTIONS
# ===========================
@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'session', 'statut', 'note_finale', 'certificat_status', 'date_inscription')
    readonly_fields = ('certificat_lien',)

    def certificat_status(self, obj):
        if obj.certificat_lien:
            return format_html('<a href="{}" target="_blank" style="color:green;">📄 Télécharger</a>', obj.certificat_lien)
        elif obj.est_terminee():
            return format_html('<span style="color:orange;">⏳ En attente</span>')
        return format_html('<span style="color:gray;">❌ Aucun</span>')
    certificat_status.short_description = "Certificat"


# ===========================
# 🧾 PROGRESSION
# ===========================
@admin.register(ChapterProgress)
class ChapterProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'chapitre', 'score', 'valide', 'date_validation')
    readonly_fields = ('date_validation',)
    ordering = ('-date_validation',)
