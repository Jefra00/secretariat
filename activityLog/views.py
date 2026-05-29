# support/views_logs.py
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import ActivityLog

@login_required
def journal_activite(request):
    """Affiche le journal d'activité (personnel ou admin complet)."""
    if request.user.is_staff:
        logs = ActivityLog.objects.all()
    else:
        logs = ActivityLog.objects.filter(user=request.user)

    paginator = Paginator(logs, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "support/journal_activite.html", {"logs": page_obj})
