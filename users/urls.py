from django.urls import path,include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views
from .views import PhoneTokenObtainPairView

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('inscription/', views.inscription_client, name='inscription_client'),
    path('connexion/', views.connexion_client, name='connexion_client'),
    path('deconnexion/', views.deconnexion_client, name='deconnexion_client'),
    path('espace/', views.espace_client, name='espace_client'),
    path('espace_admin/', views.espace_admin, name='espace_admin'),
    path('comptes/', views.comptes, name='comptes'),
    path('completer_compte/', views.creer_ou_completer_compte, name='completer_compte'),
    path('profil/modifier/', views.modifier_profil, name='modifier_profil'),
    path('services/', include('services.urls', namespace='services')),
    path('apropo/', views.apropos, name='apropo'),
    path("commandes/", include("commandes.urls")),
    path("paiements/", include("paiements.urls")),
    path("support/", include("support.urls")),
    path("communication/", include("communication.urls")),
    path("cours/", include("cours.urls")),
    path("companies/", include("companies.urls")),
    path('resto/', include('resto.urls')),
    path("auth/registere/", views.registere_user),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/login/", PhoneTokenObtainPairView.as_view()),
    path('api/', views.api, name='api'),
]
