from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import PhoneTokenObtainPairSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django import forms
from .models import User
from django.contrib.auth.decorators import login_required
from .forms import ClientLoginForm,UserCreationForm,UserForm,UserUpdateForm
from services.models import Service  # 🔥 On importe ton modèle Service
from django.contrib.auth import authenticate, login
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from users.services.hotel_api import get_hotels
from django.conf import settings
import requests




class ClientRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '••••••••',
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
            }
        ),
    )

    password2 = forms.CharField(
        label="Confirmez le mot de passe",
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '••••••••',
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
            }
        ),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telephone', 'pays', 'adresse']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Votre prénom',
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Votre nom',
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Votre email professionnel',
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
            }),
            'telephone': forms.TextInput(attrs={
                'placeholder': '+33...',
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
            }),
            'pays': forms.TextInput(attrs={
                'placeholder': 'France',
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
            }),
            'adresse': forms.TextInput(attrs={
                'placeholder': 'Adresse complète',
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email'].lower()
        user.role = 'client'
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


def inscription_client(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Votre compte client a été créé avec succès 🎉")
            return redirect('connexion_client')  # Redirige vers ton tableau de bord client
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ClientRegistrationForm()

    return render(request, 'pages/register.html', {'form': form})


def connexion_client(request):
    """
    Vue de connexion sécurisée pour les utilisateurs.
    Redirige selon le rôle (client, admin, employé) et gère la session utilisateur.
    """

    # Si déjà connecté, redirige automatiquement vers l’espace correspondant
    

    if request.method == 'POST':
        form = ClientLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # ✅ Initialisation de la session pour isoler les données
            request.session['user_id'] = user.id
            request.session['role'] = user.role
            request.session['langue'] = user.langue

            messages.success(request, f"Bienvenue {user.first_name or user.username} 👋")
            return _redirect_user_by_role(user)
        else:
            messages.error(request, "Identifiants incorrects. Veuillez réessayer.")
    else:
        form = ClientLoginForm()

    return render(request, 'pages/connexion_client.html', {'form': form})


def _redirect_user_by_role(user):
    """
    Fonction interne pour rediriger l'utilisateur vers le bon tableau de bord selon son rôle.
    """
    if user.is_superuser or user.is_admin():
        return redirect('espace_admin')
    elif user.is_client():
        return redirect('espace_client')
    elif user.is_employe():
        return redirect('espace_employe')
    else:
        return redirect('espace_client')  # fallback par défaut


def deconnexion_client(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté avec succès.")
    return redirect('connexion_client')

def accueil(request):
    # ✅ Récupère les 6 services populaires (ex: champ booléen ou score)
    services_populaires = Service.objects.filter(actif=True, populaire=True).order_by('-date_creation')[:6]

    return render(request, 'pages/accueil.html', {
        'services_populaires': services_populaires
    })

def creer_compte(request):
    return render(request, 'pages/register.html')

@login_required
def espace_client(request):
    """
    Tableau de bord du client — liste des services disponibles + statistiques de commandes
    """
    user = request.user

    # Vérification du rôle utilisateur
    if not user.is_client():
        messages.error(request, "Accès refusé 🚫")
        return redirect('connexion_client')

    # Récupération des commandes de l’utilisateur
    commandes = user.orders.all() if hasattr(user, 'orders') else []

    # Statistiques pour le tableau de bord
    commandes_total = commandes.count()
    commandes_en_cours = commandes.filter(statut='en_cours').count()
    commandes_terminees = commandes.filter(statut='termine').count()

    # Services disponibles
    services = (
        Service.objects
        .select_related('category')
        .all()
        .order_by('-populaire', 'date_creation')
    )

    # Contexte envoyé au template
    context = {
        'user': user,
        'commandes': commandes,
        'services': services,
        'commandes_total': commandes_total,
        'commandes_en_cours': commandes_en_cours,
        'commandes_terminees': commandes_terminees,
    }

    return render(request, 'espaces/espace_client.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def comptes(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            # Si le superadmin crée un compte, il peut choisir le rôle
            user.save()
            messages.success(request, "Le compte a été créé avec succès.")
            return redirect('liste_utilisateurs')
        else:
            messages.error(request, "Erreur lors de la création du compte.")
    else:
        form = UserCreationForm()

    return render(request, 'pages/comptes.html', {'form': form})

def espace_admin(request):
    return render(request, 'espaces/espace_admin.html')


def creer_ou_completer_compte(request):
    if request.user.is_authenticated:
        # Utilisateur connecté → on complète les infos manquantes
        form = UserForm(request.POST or None, request.FILES or None, user=request.user, instance=request.user)
        titre_page = "Compléter vos informations"
    else:
        # Admin ou création d’un nouveau compte
        form = UserForm(request.POST or None, request.FILES or None)
        titre_page = "Créer un compte utilisateur"

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if request.user.is_authenticated:
                messages.success(request, "Vos informations ont été complétées avec succès.")
            else:
                messages.success(request, "Le compte a été créé avec succès.")
            return redirect('espace_admin')

    return render(request, 'pages/creer_compte.html', {'form': form, 'titre_page': titre_page})


@login_required
def modifier_profil(request):
    user = request.user

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos informations ont été mises à jour avec succès ✅")
            return redirect('modifier_profil')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = UserUpdateForm(instance=user)

    return render(request, 'modifs/modifier_profil.html', {'form': form})


def apropos(request):
    return render(request, 'pages/Apropo.html')


@api_view(["POST"])
@permission_classes([AllowAny])
def registere_user(request):

    phone = request.data.get("phone")
    password = request.data.get("password")

    if not phone or not password:
        return Response({"error": "Champs manquants"}, status=400)

    if User.objects.filter(username=phone).exists():
        return Response({"error": "Numéro déjà utilisé"}, status=400)

    user = User.objects.create_user(
        username=phone,
        password=password,
        telephone=phone,   # 🔥 IMPORTANT
        role="client"      # 🔥 FORCE CLIENT
    )

    return Response({
        "message": "Compte créé",
        "user_id": user.id,
        "role": user.role
    }, status=201)

class PhoneTokenObtainPairView(TokenObtainPairView):
    serializer_class = PhoneTokenObtainPairSerializer


def apis(request):
    hotels = get_hotels()

    context = {
        "hotels": hotels
    }

    return render(request, "pag/api.html", context)


def api(request):
    offers = []

    if request.method == "POST":
        origin = request.POST.get("origin")
        destination = request.POST.get("destination")
        date = request.POST.get("date")

        url = f"{settings.DUFFEL_API_URL}/offer_requests"

        headers = {
            "Authorization": f"Bearer {settings.DUFFEL_API_KEY}",
            "Duffel-Version": "v1",
            "Content-Type": "application/json"
        }

        data = {
            "data": {
                "slices": [
                    {
                        "origin": origin,
                        "destination": destination,
                        "departure_date": date
                    }
                ],
                "passengers": [{"type": "adult"}],
                "cabin_class": "economy"
            }
        }

        response = requests.post(url, json=data, headers=headers)
        result = response.json()

        offers = result.get("data", {}).get("offers", [])

    return render(request, "pages/api.html", {"offers": offers})

def book_flight(request):
    if request.method == "POST":
        offer_id = request.POST.get("offer_id")
        amount = request.POST.get("amount")
        currency = request.POST.get("currency")

        # Simulation (sans paiement réel)
        return JsonResponse({
            "message": "Réservation simulée",
            "offer_id": offer_id,
            "amount": amount,
            "currency": currency
        })