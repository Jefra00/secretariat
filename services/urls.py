# services/urls.py
from django.urls import path
from . import views

app_name = "services"  # ✅ ajoute un namespace pour éviter le NoReverseMatch

urlpatterns = [
    path('', views.services, name='liste'),  # Liste de tous les services
    path('<slug:slug>/', views.detail_service, name='detail'),  # Détail d’un service
]
