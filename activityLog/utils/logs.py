# utils/logs.py
from .models import ActivityLog

def log_action(request, categorie, action, description="", succes=True, objet=None):
    """Enregistre une action utilisateur dans le journal d'activité."""
    user = request.user if request.user.is_authenticated else None
    ip = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

    ActivityLog.enregistrer(
        user=user,
        categorie=categorie,
        action=action,
        description=description,
        ip=ip,
        user_agent=user_agent,
        succes=succes,
        objet=objet,
    )

def get_client_ip(request):
    """Détecte l’adresse IP réelle du client."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
