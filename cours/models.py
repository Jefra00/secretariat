from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid


class Course(models.Model):
    """Cours ou module de formation proposé sur la plateforme."""

    MODE = [
        ('en_ligne', 'En ligne'),
        ('presentiel', 'Présentiel'),
        ('hybride', 'Hybride'),
    ]

    NIVEAUX = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
        ('professionnel', 'Professionnel'),
    ]

    id_public = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    titre = models.CharField(max_length=200)
    description = models.TextField()
    niveau = models.CharField(max_length=50, choices=NIVEAUX, default='debutant')
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    duree = models.CharField(max_length=50, help_text="Ex: 3 jours, 2 semaines")
    mode = models.CharField(max_length=20, choices=MODE, default='en_ligne')
    image_couverture = models.ImageField(upload_to='courses/covers/', blank=True, null=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    nombre_participants = models.PositiveIntegerField(default=0)
    certificat_disponible = models.BooleanField(default=True)
    video_intro = models.URLField(blank=True, null=True, help_text="Vidéo d’introduction publique du cours")
    presentation_ai = models.TextField(blank=True, null=True, help_text="Résumé automatique IA du contenu du cours")

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Cours"
        verbose_name_plural = "Cours"

    def __str__(self):
        return self.titre
    def generer_resume_ia(self):
        """
        Génère automatiquement un résumé persuasif du cours
        grâce à l’API OpenAI (GPT-4 ou GPT-4o-mini)
        """
        try:
            openai.api_key = settings.OPENAI_API_KEY
            prompt = (
                f"Rédige un résumé concis, persuasif et professionnel pour une page de formation intitulée '{self.titre}'. "
                f"Voici la description du cours : {self.description[:800]}. "
                f"Adopte un ton motivant et clair pour encourager les apprenants à s’inscrire."
            )

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=120,
            )

            self.presentation_ai = response.choices[0].message['content']
            self.save(update_fields=['presentation_ai'])
            return self.presentation_ai

        except Exception as e:
            print("⚠️ Erreur IA :", e)
            return None
    # ✅ Durée en jours (si format numérique)
    def duree_estimee(self):
        if any(c.isdigit() for c in self.duree):
            return ''.join([c for c in self.duree if c.isdigit()]) + " jours"
        return self.duree

    # ✅ Mise à jour automatique du nombre d’inscriptions
    def update_nombre_participants(self):
        self.nombre_participants = self.inscriptions.count()
        self.save(update_fields=['nombre_participants'])

    # ✅ Récupérer les sessions actives
    def sessions_actives(self):
        return self.sessions.filter(date_fin__gte=timezone.now().date())

    # ✅ Statut de publication
    def statut(self):
        return "Actif" if self.actif else "Archivé"
    
    def generer_resume_ia(self):
        """Simule une génération IA d’un résumé intelligent du cours"""
        self.presentation_ai = f"Ce cours '{self.titre}' vous permettra d’acquérir les compétences essentielles pour devenir un professionnel du secrétariat. Niveau : {self.get_niveau_display()}."
        self.save(update_fields=['presentation_ai'])


class Chapter(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chapitres')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    ordre = models.PositiveIntegerField(default=1)
    controle_obligatoire = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Chapitre"
        verbose_name_plural = "Chapitres"

    def __str__(self):
        return f"{self.course.titre} - Chapitre {self.ordre}: {self.titre}"

    # 🔹 Vérifie si le chapitre est validé par un utilisateur
    def est_valide_pour(self, user):
        return ChapterProgress.objects.filter(chapitre=self, user=user, valide=True).exists()

# ----------------------------------------------------------
# 🎬 LEÇONS VIDÉO DANS LES CHAPITRES
# ----------------------------------------------------------
class Lesson(models.Model):
    chapitre = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='lecons')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    duree_video = models.CharField(max_length=20, blank=True, null=True)
    ressource_pdf = models.FileField(upload_to='courses/pdf/', blank=True, null=True)
    ordre = models.PositiveIntegerField(default=1)
    transcript_auto = models.TextField(blank=True, null=True, help_text="Transcription automatique IA")
    retro_ai = models.TextField(blank=True, null=True, help_text="Analyse IA du contenu vidéo")

    class Meta:
        ordering = ['ordre']
        verbose_name = "Leçon"
        verbose_name_plural = "Leçons"

    def __str__(self):
        return f"{self.chapitre.titre} - {self.titre}"

    # 🔹 Analyse IA fictive pour la rétroaction automatique
    def generer_retro_ai(self):
        self.retro_ai = f"Analyse intelligente : la leçon '{self.titre}' aide à renforcer les compétences clés du module {self.chapitre.titre}."
        self.save(update_fields=['retro_ai'])

# ----------------------------------------------------------
# 🧠 CONTROLES DE CONNAISSANCES
# ----------------------------------------------------------
class KnowledgeCheck(models.Model):
    chapitre = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='quiz')
    question = models.TextField()
    choix = models.JSONField(
    default=list,
    help_text="Ex: [{'reponse':'A', 'texte':'Option A'},...]"
)

    bonne_reponse = models.CharField(max_length=10)
    feedback = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Contrôle de connaissance"
        verbose_name_plural = "Contrôles de connaissance"

    def __str__(self):
        return f"Quiz - {self.chapitre.titre}"

    # ✅ Vérification de la réponse
    def verifier(self, reponse):
        return reponse.strip().lower() == self.bonne_reponse.strip().lower()


# ----------------------------------------------------------
# 🧩 PROGRESSION UTILISATEUR DANS LES CHAPITRES
# ----------------------------------------------------------
class ChapterProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chapitre = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    valide = models.BooleanField(default=False)
    date_validation = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'chapitre')

    def __str__(self):
        return f"{self.user.username} - {self.chapitre.titre}"

    def valider(self, score):
        self.score = score
        self.valide = True
        self.date_validation = timezone.now()
        self.save()

class CourseSession(models.Model):
    """Session spécifique d’un cours (par formateur, date, lieu)."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    formateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sessions_formateur')
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    lieu = models.CharField(max_length=200, blank=True, null=True)
    capacite_max = models.PositiveIntegerField(default=30)
    inscrits = models.PositiveIntegerField(default=0)
    note_moyenne = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    statut = models.CharField(max_length=30, default='ouverte', choices=[
        ('ouverte', 'Ouverte'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ])

    class Meta:
        ordering = ['-date_debut']
        verbose_name = "Session de cours"
        verbose_name_plural = "Sessions de cours"

    def __str__(self):
        return f"{self.course.titre} - {self.date_debut.strftime('%d/%m/%Y')}"

    # ✅ Déterminer si la session est actuellement en cours
    def est_active(self):
        today = timezone.now().date()
        return self.date_debut <= today <= (self.date_fin or today)

    # ✅ Calcul automatique du nombre d’inscrits
    def update_inscrits(self):
        self.inscrits = self.inscriptions_session.count()
        self.save(update_fields=['inscrits'])

    # ✅ Taux d’occupation
    def taux_occupation(self):
        if self.capacite_max == 0:
            return 0
        return round((self.inscrits / self.capacite_max) * 100, 2)

    # ✅ Durée réelle de la session
    def duree_jours(self):
        if not self.date_fin:
            return 1
        return (self.date_fin - self.date_debut).days + 1

class CourseEnrollment(models.Model):
    """Inscription d’un utilisateur à un cours."""

    STATUTS = [
        ('inscrit', 'Inscrit'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('abandonne', 'Abandonné'),
        ('attente_paiement', 'En attente de paiement'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='inscriptions')
    session = models.ForeignKey(CourseSession, on_delete=models.SET_NULL, null=True, blank=True, related_name='inscriptions_session')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inscriptions_cours')
    statut = models.CharField(max_length=50, choices=STATUTS, default='inscrit')
    date_inscription = models.DateTimeField(auto_now_add=True)
    note_finale = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    certificat_lien = models.URLField(blank=True, null=True)
    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_inscription']
        unique_together = ('course', 'user')
        verbose_name = "Inscription à un cours"
        verbose_name_plural = "Inscriptions aux cours"

    def __str__(self):
        return f"{self.user.username} → {self.course.titre}"

    # ✅ Vérifie si la formation est terminée
    def est_terminee(self):
        return self.statut == 'termine'

    # ✅ Génère un certificat (fictif ou via un service externe)
    def generer_certificat(self):
        if self.course.certificat_disponible and self.est_terminee():
            self.certificat_lien = f"https://plateforme.com/certificats/{self.user.id}-{self.course.id}.pdf"
            self.save(update_fields=['certificat_lien'])
            return self.certificat_lien
        return None

    # ✅ Mise à jour automatique du statut
    def update_statut(self, nouveau_statut):
        self.statut = nouveau_statut
        self.save(update_fields=['statut'])
    
    # ✅ Mise à jour automatique de la progression
    def update_progression(self):
        total = self.course.chapitres.count()
        valides = ChapterProgress.objects.filter(user=self.user, chapitre__course=self.course, valide=True).count()
        self.progression = (valides / total) * 100 if total > 0 else 0
        if self.progression == 100:
            self.statut = 'termine'
        self.save()


