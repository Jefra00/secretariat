# middlewares/activity_log_middleware.py
from django.utils.deprecation import MiddlewareMixin
from support.models import ActivityLog
from utils.logs import get_client_ip

class ActivityLogMiddleware(MiddlewareMixin):
    """Log automatiquement les connexions et déconnexions."""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            if not hasattr(request.user, "_log_connected"):
                ActivityLog.enregistrer(
                    user=request.user,
                    categorie="connexion",
                    action="Connexion réussie",
                    ip=get_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
                    succes=True,
                )
                request.user._log_connected = True  # éviter doublon
        return None

    def process_response(self, request, response):
        # Déconnexion détectée
        if getattr(request, "user", None) and not request.user.is_authenticated:
            ActivityLog.enregistrer(
                user=None,
                categorie="deconnexion",
                action="Utilisateur déconnecté",
                succes=True,
            )
        return response
