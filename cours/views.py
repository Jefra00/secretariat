from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Course, CourseSession, CourseEnrollment


# 🧭 Liste des cours
def course_list(request):
    courses_list = Course.objects.filter(actif=True).order_by('-id')  # plus récents d'abord
    paginator = Paginator(courses_list, 6)  # 6 cours par page (tu peux ajuster)

    page_number = request.GET.get('page')
    courses = paginator.get_page(page_number)

    return render(request, "elearning/course_list.html", {"courses": courses})


# 📘 Détail d’un cours
def course_detail(request, pk):
    """Page de détail d’un cours."""
    course = get_object_or_404(Course, pk=pk, actif=True)
    sessions = course.sessions_actives()

    # Vérifie si l’utilisateur est inscrit
    inscrit = False
    if request.user.is_authenticated:
        inscrit = CourseEnrollment.objects.filter(course=course, user=request.user).exists()

    context = {
        "course": course,
        "sessions": sessions,
        "inscrit": inscrit,
    }
    return render(request, "elearning/course_detail.html", context)

# 🗓️ Détail d’une session de cours
def session_detail(request, session_id):
    session = get_object_or_404(CourseSession, pk=session_id)
    return render(request, "elearning/session_detail.html", {"session": session})


# 🧾 Inscription à un cours
@login_required
def inscrire_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if CourseEnrollment.objects.filter(course=course, user=request.user).exists():
        messages.warning(request, "Vous êtes déjà inscrit à ce cours.")
        return redirect("elearning:dashboard")

    if request.method == "POST":
        session_id = request.POST.get("session")
        session = CourseSession.objects.filter(id=session_id).first() if session_id else None
        inscription = CourseEnrollment.objects.create(
            course=course,
            session=session,
            user=request.user,
            statut="inscrit"
        )
        course.update_nombre_participants()
        if session:
            session.update_inscrits()
        messages.success(request, f"✅ Inscription réussie à « {course.titre} » !")
        return redirect("elearning:dashboard")

    sessions = course.sessions_actives()
    return render(request, "elearning/form_course_enroll.html", {
        "course": course,
        "sessions": sessions
    })


# 🎓 Tableau de bord de l’apprenant
@login_required
def dashboard(request):
    inscriptions = request.user.inscriptions_cours.select_related("course", "session")
    return render(request, "elearning/enrollment_dashboard.html", {
        "inscriptions": inscriptions
    })


# 🪪 Téléchargement du certificat
@login_required
def telecharger_certificat(request, enrollment_id):
    inscription = get_object_or_404(CourseEnrollment, id=enrollment_id, user=request.user)
    if not inscription.est_terminee():
        messages.error(request, "Le certificat n’est disponible qu’après la fin du cours.")
        return redirect("elearning:dashboard")

    certificat_url = inscription.generer_certificat()
    return render(request, "elearning/enrollment_certificate.html", {
        "inscription": inscription,
        "certificat_url": certificat_url
    })
