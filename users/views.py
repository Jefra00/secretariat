from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django import forms
from django.conf import settings
import requests
import uuid

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authtoken.models import Token

from .models import User, Livraison
from .forms import ClientLoginForm, UserCreationForm, UserForm, UserUpdateForm
from .serializers import PhoneTokenObtainPairSerializer
from users.services.hotel_api import get_hotels




_F = (
    'w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm '
    'focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 outline-none transition'
)


class ClientRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': _F}),
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': _F}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'telephone', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Votre nom complet',
                'class': _F,
            }),
            'telephone': forms.TextInput(attrs={
                'placeholder': '+242 06 000 00 00',
                'class': _F,
                'inputmode': 'tel',
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'exemple@mail.com (optionnel)',
                'class': _F,
            }),
        }

    def clean_telephone(self):
        phone = self.cleaned_data.get('telephone', '').replace(' ', '').replace('-', '')
        if not phone:
            raise forms.ValidationError("Le numéro de téléphone est obligatoire.")
        if User.objects.filter(telephone=phone).exists():
            raise forms.ValidationError("Un compte existe déjà avec ce numéro.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email and User.objects.filter(email=email).exists():
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
        phone = self.cleaned_data['telephone'].replace(' ', '').replace('-', '')
        user.telephone = phone
        user.username  = phone          # username = telephone pour unicité
        user.role      = 'client'
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


def inscription_client(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Compte créé avec succès. Connectez-vous pour accéder à votre espace.")
            return redirect('connexion_client')
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
    # Déjà authentifié → rediriger immédiatement (empêche le retour arrière vers login)
    if request.user.is_authenticated:
        return _redirect_user_by_role(request.user)

    next_url = request.GET.get('next') or request.POST.get('next', '')

    if request.method == 'POST':
        form = ClientLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='users.backends.PhoneAuthBackend')

            request.session['user_id'] = user.id
            request.session['role'] = user.role
            request.session['langue'] = user.langue
            # Nonce de session : lie cette session à la fenêtre du navigateur (isolation cross-browser)
            request.session['auth_nonce'] = uuid.uuid4().hex[:20]

            # Sauvegarder position GPS si livreur et coordonnées fournies
            if user.role == 'livreur':
                try:
                    gps_lat = request.POST.get('gps_lat', '').strip()
                    gps_lng = request.POST.get('gps_lng', '').strip()
                    if gps_lat and gps_lng:
                        from django.contrib.gis.geos import Point
                        from django.utils import timezone as tz
                        user.last_lat = float(gps_lat)
                        user.last_lng = float(gps_lng)
                        user.last_location = Point(float(gps_lng), float(gps_lat), srid=4326)
                        user.location_updated_at = tz.now()
                        user.save(update_fields=['last_lat', 'last_lng', 'last_location', 'location_updated_at'])
                except Exception:
                    pass

            messages.success(request, f"Bienvenue {user.first_name or user.username} 👋")

            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return _redirect_user_by_role(user)
        else:
            messages.error(request, "Identifiants incorrects. Veuillez réessayer.")
    else:
        form = ClientLoginForm()

    return render(request, 'pages/connexion_client.html', {'form': form, 'next': next_url})


def _redirect_user_by_role(user):
    """Redirige vers le bon tableau de bord selon le rôle."""
    if user.is_superuser or user.is_admin():
        return redirect('espace_admin')
    elif user.is_client():
        return redirect('espace_client')
    elif user.is_employe():
        return redirect('gestion_commandes')
    elif user.is_vendeur():
        return redirect('vendeur_dashboard')
    elif user.role == 'livreur':
        return redirect('livreur_dashboard')
    else:
        return redirect('espace_client')


def deconnexion_client(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté avec succès.")
    return redirect('connexion_client')

def accueil(request):
    return render(request, 'pages/accueil.html')

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

    from resto.models import Order as RestoOrder
    commandes = RestoOrder.objects.filter(user=user)
    commandes_total = commandes.count()
    commandes_en_cours = commandes.filter(status='in_progress').count()
    commandes_terminees = commandes.filter(status='done').count()

    context = {
        'user': user,
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
            return redirect('espace_admin')
        else:
            messages.error(request, "Erreur lors de la création du compte.")
    else:
        form = UserCreationForm()

    return render(request, 'pages/comptes.html', {'form': form})

@login_required
def espace_admin(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.error(request, "Accès refusé.")
        return redirect('connexion_client')
    return redirect('admin_panel_dashboard')


def creer_ou_completer_compte(request):
    if request.user.is_authenticated:
        # Utilisateur connecté → on complète les infos manquantes
        form = UserForm(request.POST or None, request.FILES or None, user=request.user, instance=request.user)
        titre_page = "Compléter vos informations"
    else:
        # Admin ou création d'un nouveau compte
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_fcm_token(request):
    token = request.data.get("fcm_token", "").strip()
    if not token:
        return Response({"error": "fcm_token manquant"}, status=400)
    request.user.fcm_token = token
    request.user.save(update_fields=["fcm_token"])
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "telephone": user.telephone or user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role,
        "date_inscription": user.date_inscription,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_orders(request):
    from resto.models import Order
    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items__dish")
        .select_related("livreur")
        .order_by("-created_at")
    )
    data = []
    for order in orders:
        items = [
            {
                "dish_id": item.dish.id,
                "dish_title": item.dish.title,
                "dish_image": request.build_absolute_uri(item.dish.image) if item.dish.image else "",
                "quantity": item.quantity,
                "line_price": float(item.line_price),
            }
            for item in order.items.all()
        ]

        livreur_data = None
        if order.livreur:
            lv = order.livreur
            try:
                profile = lv.livreur_profile
                livreur_data = {
                    "id": lv.id,
                    "nom": lv.get_full_name() or lv.username,
                    "telephone": lv.telephone or "",
                    "photo_url": profile.photo_url,
                    "matricule_moto": profile.matricule_moto,
                }
            except Exception:
                livreur_data = {
                    "id": lv.id,
                    "nom": lv.get_full_name() or lv.username,
                    "telephone": lv.telephone or "",
                    "photo_url": "",
                    "matricule_moto": "NC",
                }

        data.append({
            "id": order.id,
            "status": order.status,
            "status_display": order.get_status_display(),
            "created_at": order.created_at,
            "total": float(order.total),
            "subtotal": float(order.subtotal),
            "delivery_fee": float(order.delivery_fee),
            "delivery_address": order.delivery_address,
            "qr_code": order.qr_code,
            "livreur": livreur_data,
            "items": items,
            "gps_lat": float(order.delivery_lat) if getattr(order, 'delivery_lat', None) else None,
            "gps_lng": float(order.delivery_lng) if getattr(order, 'delivery_lng', None) else None,
        })
    return Response(data)


# ──────────────────────────────────────────────────────────────────────────────
# API MOBILE — CLIENT
# ──────────────────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_client_commandes(request):
    """Liste des Paiement du client connecté (pour l'app mobile)."""
    import json as _json
    from .models import Paiement
    paiements = (
        Paiement.objects
        .filter(client=request.user)
        .select_related('livraison', 'livraison__livreur')
        .order_by('-cree_le')
    )
    data = []
    for p in paiements:
        try:
            liv = p.livraison
            livraison_data = {
                "pk": liv.pk,
                "statut": liv.statut,
                "statut_display": liv.get_statut_display(),
                "livreur_nom": liv.livreur.get_full_name() if liv.livreur else "",
            }
        except Exception:
            livraison_data = None

        try:
            notes = _json.loads(p.notes) if p.notes else []
        except Exception:
            notes = []

        data.append({
            "pk": p.pk,
            "section": p.section,
            "section_display": p.get_section_display(),
            "statut": p.statut,
            "statut_display": p.get_statut_display(),
            "methode": p.methode,
            "methode_display": p.get_methode_display(),
            "mode_livraison": p.mode_livraison,
            "mode_livraison_display": p.get_mode_livraison_display(),
            "montant": float(p.montant),
            "frais_livraison": float(p.frais_livraison),
            "frais_service": float(p.frais_service),
            "montant_total": float(p.montant_total),
            "quartier_livraison": p.quartier_livraison or "",
            "adresse_livraison": p.adresse_livraison or "",
            "cree_le": p.cree_le,
            "items": notes,
            "livraison": livraison_data,
        })
    return Response(data)


# ──────────────────────────────────────────────────────────────────────────────
# API MOBILE — LIVREUR (Livraison objects)
# ──────────────────────────────────────────────────────────────────────────────

def _liv_to_dict(liv):
    p = liv.paiement
    return {
        "pk": liv.pk,
        "statut": liv.statut,
        "statut_display": liv.get_statut_display(),
        "otp_valide": liv.otp_valide,
        "created_at": liv.created_at,
        "updated_at": liv.updated_at if hasattr(liv, 'updated_at') else liv.created_at,
        "paiement": {
            "pk": p.pk,
            "section": p.section,
            "section_display": p.get_section_display(),
            "montant_total": float(p.montant_total),
            "frais_livraison": float(p.frais_livraison) if hasattr(p, 'frais_livraison') and p.frais_livraison else 0.0,
            "quartier_livraison": p.quartier_livraison or "",
            "adresse_livraison": p.adresse_livraison or "",
            "gps_lat": float(p.gps_lat) if p.gps_lat else None,
            "gps_lng": float(p.gps_lng) if p.gps_lng else None,
            "client_nom": p.client.get_full_name() if p.client else "",
            "client_telephone": p.client.telephone or "" if p.client else "",
        },
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_livreur_livraisons(request):
    """Disponibles + mes missions actives + historique + stats pour le livreur mobile."""
    if request.user.role != 'livreur':
        return Response({"error": "forbidden"}, status=403)

    from django.db.models import Sum
    from django.utils import timezone as _tz
    import datetime as _dt

    disponibles = (
        Livraison.objects
        .filter(statut='attente_livreur')
        .select_related('paiement', 'paiement__client')
        .order_by('-created_at')
    )
    mes_missions = (
        Livraison.objects
        .filter(livreur=request.user)
        .exclude(statut__in=['livree', 'echouee'])
        .select_related('paiement', 'paiement__client')
        .order_by('-created_at')
    )
    historique = (
        Livraison.objects
        .filter(livreur=request.user, statut__in=['livree', 'echouee'])
        .select_related('paiement', 'paiement__client')
        .order_by('-created_at')[:60]
    )

    today      = _tz.now().date()
    week_start = today - _dt.timedelta(days=today.weekday())
    livrees_qs = Livraison.objects.filter(livreur=request.user, statut='livree')
    total_livrees  = livrees_qs.count()
    gains_total    = livrees_qs.aggregate(s=Sum('paiement__frais_livraison'))['s'] or 0
    gains_semaine  = livrees_qs.filter(created_at__date__gte=week_start).aggregate(
        s=Sum('paiement__frais_livraison'))['s'] or 0
    gains_auj      = livrees_qs.filter(created_at__date=today).aggregate(
        s=Sum('paiement__frais_livraison'))['s'] or 0

    return Response({
        "disponibles":  [_liv_to_dict(l) for l in disponibles],
        "mes_missions": [_liv_to_dict(l) for l in mes_missions],
        "historique":   [_liv_to_dict(l) for l in historique],
        "stats": {
            "total_livrees":   total_livrees,
            "gains_total":     float(gains_total),
            "gains_semaine":   float(gains_semaine),
            "gains_aujourd_hui": float(gains_auj),
        },
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_livreur_accepter(request, pk):
    """Accepter une mission disponible."""
    if request.user.role != 'livreur':
        return Response({"error": "forbidden"}, status=403)
    from django.db import transaction
    from django.utils import timezone as _tz
    with transaction.atomic():
        liv = get_object_or_404(
            Livraison.objects.select_for_update(),
            pk=pk, statut__in=['attente_livreur', 'assigne'],
        )
        if liv.statut == 'assigne' and liv.livreur and liv.livreur != request.user:
            return Response({"error": "Cette mission est déjà assignée à un autre livreur"}, status=409)
        liv.livreur = request.user
        liv.livreur_nom_cache = request.user.get_full_name()
        liv.statut = 'accepte'
        liv.accepted_at = _tz.now()
        liv.save(update_fields=['livreur', 'livreur_nom_cache', 'statut', 'accepted_at'])
    if liv.paiement.client and liv.paiement.client.fcm_token:
        try:
            from resto.services.fcm_service import send_push_notification
            nom = request.user.get_full_name() or request.user.username
            send_push_notification(
                fcm_token=liv.paiement.client.fcm_token,
                title="🛵 Livreur en route vers le vendeur !",
                body=f"{nom} est en route pour récupérer votre commande.",
                data={"livraison_id": str(liv.pk), "paiement_id": str(liv.paiement_id), "type": "livreur_assigned"},
            )
        except Exception:
            pass
    return Response({"ok": True, "statut": liv.statut})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_livreur_statut(request, pk):
    """Mettre à jour le statut d'une mission selon la machine d'état stricte."""
    if request.user.role != 'livreur':
        return Response({"error": "forbidden"}, status=403)
    liv = get_object_or_404(Livraison, pk=pk, livreur=request.user)
    nouveau = request.data.get("statut", "")
    # Machine d'état : transitions autorisées uniquement (livree nécessite OTP via /otp/)
    TRANSITIONS = {
        'accepte':         ['en_recuperation', 'echouee'],
        'en_recuperation': ['en_route',         'echouee'],
        'en_route':        ['echouee'],
    }
    autorisees = TRANSITIONS.get(liv.statut, [])
    if nouveau not in autorisees:
        return Response(
            {"error": f"Transition '{liv.statut}' → '{nouveau}' non autorisée"},
            status=400,
        )
    from django.utils import timezone as _tz
    liv.statut = nouveau
    if nouveau == 'en_recuperation':
        liv.picked_at = _tz.now()
    liv.save()
    # Notifier le client et envoyer l'OTP quand le livreur est en route
    if liv.paiement.client and liv.paiement.client.fcm_token:
        try:
            from resto.services.fcm_service import send_push_notification
            if nouveau == 'en_route':
                send_push_notification(
                    fcm_token=liv.paiement.client.fcm_token,
                    title="🛵 Votre livreur est en route !",
                    body=f"Code de confirmation : {liv.otp_code} — À remettre au livreur à la réception.",
                    data={"livraison_id": str(liv.pk), "paiement_id": str(liv.paiement_id), "otp": liv.otp_code, "type": "livreur_en_route"},
                )
            elif nouveau == 'echouee':
                send_push_notification(
                    fcm_token=liv.paiement.client.fcm_token,
                    title="⚠️ Livraison échouée",
                    body="La livraison de votre commande a échoué. Contactez le support.",
                    data={"livraison_id": str(liv.pk), "paiement_id": str(liv.paiement_id), "type": "livraison_echouee"},
                )
            else:
                send_push_notification(
                    fcm_token=liv.paiement.client.fcm_token,
                    title="📦 Récupération du colis en cours",
                    body="Le livreur est chez le vendeur et récupère votre commande.",
                    data={"livraison_id": str(liv.pk), "paiement_id": str(liv.paiement_id), "type": "livraison_update"},
                )
        except Exception:
            pass
    return Response({"ok": True, "statut": liv.statut})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_livreur_mission_map(request, pk):
    """Positions client/vendeur/livreur pour la carte mobile."""
    import json as _json
    if request.user.role != 'livreur':
        return Response({"error": "forbidden"}, status=403)
    liv = get_object_or_404(Livraison, pk=pk, livreur=request.user)
    p = liv.paiement

    client_pos = None
    if p.gps_lat and p.gps_lng:
        client_pos = {"lat": float(p.gps_lat), "lng": float(p.gps_lng)}

    vendor_pos = None
    try:
        items = _json.loads(p.notes) if p.notes else []
        nom_boutique = None
        for item in items[:1]:
            nom_boutique = item.get('vendeur') or item.get('boutique') or item.get('shop')
        if nom_boutique:
            from boutique.models import Boutique as _Boutique
            b = _Boutique.objects.filter(nom=nom_boutique).first()
            if b and b.position_lat and b.position_lng:
                vendor_pos = {"lat": float(b.position_lat), "lng": float(b.position_lng)}
    except Exception:
        pass

    livreur_pos = None
    lv = liv.livreur
    if lv and lv.last_lat and lv.last_lng:
        livreur_pos = {"lat": float(lv.last_lat), "lng": float(lv.last_lng)}

    try:
        items = _sanitize_cart_items(_json.loads(p.notes)) if p.notes else []
    except Exception:
        items = []

    return Response({
        "statut": liv.statut,
        "statut_display": liv.get_statut_display(),
        "otp_valide": liv.otp_valide,
        "client":  client_pos,
        "vendeur": vendor_pos,
        "livreur": livreur_pos,
        "paiement": {
            "pk":               p.pk,
            "section":          p.section,
            "section_display":  p.get_section_display() if hasattr(p, 'get_section_display') else p.section,
            "montant_total":    float(p.montant_total),
            "frais_livraison":  float(p.frais_livraison) if hasattr(p, 'frais_livraison') and p.frais_livraison else 0.0,
            "mode_livraison":   p.mode_livraison,
            "quartier":         p.quartier_livraison or "",
            "adresse":          p.adresse_livraison or "",
            "client_nom":       p.client.get_full_name() if p.client else "",
            "client_telephone": (p.client.telephone or "") if p.client else "",
            "items_count":      len(items),
            "items":            items,
            "vendeur_nom":      (items[0].get('vendeur') or items[0].get('shop') or '') if items else "",
        },
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_paiement_creer(request):
    """Créer un Paiement générique depuis l'app mobile (sections boutique)."""
    import json as _json
    import random
    from .models import Paiement
    data = request.data

    section = data.get("section", "").strip()
    if not section:
        return Response({"error": "section requise"}, status=400)
    items = data.get("items", [])
    if not items:
        return Response({"error": "Le panier est vide"}, status=400)

    methode_map = {
        "mtn":    "mtn_mobile",
        "airtel": "airtel_money",
        "orange": "orange_money",
    }
    methode = methode_map.get(data.get("payment_method", ""), "autre")
    mode = "livraison" if data.get("delivery_mode") == "livraison" else "retrait"
    tel_mm = data.get("phone", "").strip()
    MOBILE_MONEY = {'mtn_mobile', 'airtel_money', 'orange_money'}
    statut_init = 'valide' if (methode in MOBILE_MONEY and tel_mm) else 'en_attente'

    gps_lat = data.get("delivery_lat") or None
    gps_lng = data.get("delivery_lng") or None
    gps_missing = mode == "livraison" and not (gps_lat and gps_lng)

    paiement = Paiement.objects.create(
        client=request.user,
        section=section,
        montant=float(data.get("subtotal", 0)),
        frais_livraison=float(data.get("delivery_cost", 0)),
        frais_service=float(data.get("service_fee", 0)),
        montant_total=float(data.get("total", 0)),
        methode=methode,
        telephone_paiement=tel_mm,
        mode_livraison=mode,
        quartier_livraison=data.get("quartier", ""),
        adresse_livraison=data.get("adresse", ""),
        gps_lat=gps_lat,
        gps_lng=gps_lng,
        notes=_json.dumps(items, ensure_ascii=False),
        statut=statut_init,
    )

    if mode == "livraison":
        otp = str(random.randint(100000, 999999))
        Livraison.objects.create(
            paiement=paiement,
            statut='attente_livreur',
            otp_code=otp,
        )
        try:
            from resto.services.fcm_service import send_push_notification
            # Étape 1 : confirmer la commande au client
            if request.user.fcm_token:
                send_push_notification(
                    fcm_token=request.user.fcm_token,
                    title="✅ Commande reçue !",
                    body="Nous recherchons un livreur disponible. Vous serez notifié(e) dès qu'un livreur est assigné.",
                    data={"paiement_id": str(paiement.pk), "type": "commande_recue"},
                )
            # Notifier les livreurs disponibles
            from resto.models import LivreurProfile
            livreurs = (
                LivreurProfile.objects
                .filter(disponible=True, user__role='livreur')
                .exclude(user__fcm_token__isnull=True)
                .exclude(user__fcm_token='')
                .select_related('user')
            )
            for lp in livreurs:
                send_push_notification(
                    fcm_token=lp.user.fcm_token,
                    title="🛵 Nouvelle mission disponible !",
                    body=f"Commande #{paiement.pk} — {paiement.quartier_livraison} — {float(paiement.montant_total):.0f} FCFA",
                    data={"paiement_id": str(paiement.pk), "type": "new_paiement"},
                )
        except Exception:
            pass

    resp = {"ok": True, "paiement_id": paiement.pk, "statut": statut_init}
    if gps_missing:
        resp["warning"] = "GPS non fourni : l'assignation automatique d'un livreur ne sera pas possible."
    return Response(resp, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_livreur_valider_otp(request, pk):
    """Valide le code OTP depuis l'app mobile (JWT auth)."""
    if request.user.role != 'livreur':
        return Response({"error": "forbidden"}, status=403)
    liv = get_object_or_404(Livraison, pk=pk, livreur=request.user, statut='en_route')
    otp_saisi = request.data.get('otp', '').strip()
    if otp_saisi != liv.otp_code:
        return Response({"ok": False, "error": "Code OTP incorrect"}, status=400)
    from django.utils import timezone as _tz
    liv.statut = 'livree'
    liv.otp_valide = True
    liv.delivered_at = _tz.now()
    liv.save()
    liv.paiement.statut = 'valide'
    liv.paiement.save(update_fields=['statut'])
    if liv.paiement.client and liv.paiement.client.fcm_token:
        try:
            from resto.services.fcm_service import send_push_notification
            send_push_notification(
                fcm_token=liv.paiement.client.fcm_token,
                title="✅ Commande livrée !",
                body="Votre commande a été livrée. Merci !",
                data={"livraison_id": str(liv.pk), "paiement_id": str(liv.paiement_id), "type": "livraison_done"},
            )
        except Exception:
            pass
    return Response({"ok": True, "statut": "livree"})


def apis(request):
    hotels, error = get_hotels()

    context = {
        "hotels": hotels,
        "error": error,
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

# ──────────────────────────────────────────────────────────────────────────────
# INTERFACE WEB LIVREUR
# ──────────────────────────────────────────────────────────────────────────────

def livreur_inscription(request):
    error = None
    if request.method == 'POST':
        prenom    = request.POST.get('prenom', '').strip()
        nom       = request.POST.get('nom', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        password  = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        matricule = request.POST.get('matricule', '').strip()
        photo_url = request.POST.get('photo_url', '').strip()
        if photo_url.startswith('data:'):
            photo_url = ''
        elif len(photo_url) > 2000:
            photo_url = ''
        ville_depart = request.POST.get('ville_depart', '').strip()
        latitude_str  = request.POST.get('latitude', '').strip()
        longitude_str = request.POST.get('longitude', '').strip()

        if not all([prenom, nom, telephone, password, matricule]):
            error = "Tous les champs obligatoires (*) doivent être remplis."
        elif password != password2:
            error = "Les mots de passe ne correspondent pas."
        elif len(password) < 6:
            error = "Le mot de passe doit contenir au moins 6 caractères."
        elif User.objects.filter(username=telephone).exists():
            error = "Ce numéro de téléphone est déjà utilisé."
        else:
            lat = float(latitude_str)  if latitude_str  else None
            lng = float(longitude_str) if longitude_str else None

            user = User.objects.create_user(
                username=telephone,
                password=password,
                first_name=prenom,
                last_name=nom,
                telephone=telephone,
                role='livreur',
            )

            # Sauvegarder la position de départ
            if lat and lng:
                from django.contrib.gis.geos import Point
                from django.utils import timezone as tz
                user.last_lat = lat
                user.last_lng = lng
                user.last_location = Point(lng, lat, srid=4326)
                user.location_updated_at = tz.now()
                user.save(update_fields=['last_lat', 'last_lng', 'last_location', 'location_updated_at'])

            from resto.models import LivreurProfile
            lp = LivreurProfile(
                user=user,
                matricule_moto=matricule,
                photo_url=photo_url,
            )
            if lat and lng:
                from django.contrib.gis.geos import Point
                from django.utils import timezone as tz
                lp.latitude = lat
                lp.longitude = lng
                lp.location = Point(lng, lat, srid=4326)
                lp.location_updated_at = tz.now()
            lp.save()

            login(request, user, backend='users.backends.PhoneAuthBackend')
            messages.success(request, f"Bienvenue {prenom} ! Votre compte livreur a été créé.")
            return redirect('livreur_dashboard')

    return render(request, 'livreur/inscription.html', {'error': error})


def livreur_connexion(request):
    if request.user.is_authenticated and request.user.role == 'livreur':
        return redirect('livreur_dashboard')
    error = None
    if request.method == 'POST':
        telephone = request.POST.get('telephone', '').strip()
        password  = request.POST.get('password', '')

        user = authenticate(request, username=telephone, password=password)
        if user is None:
            error = "Numéro de téléphone ou mot de passe incorrect."
        elif user.role != 'livreur':
            error = "Ce compte n'est pas un compte livreur."
        else:
            login(request, user)
            return redirect('livreur_dashboard')

    return render(request, 'livreur/connexion.html', {'error': error})


@login_required(login_url='/connexion/livreur/')
def livreur_dashboard(request):
    if request.user.role != 'livreur':
        return redirect('livreur_connexion')
    return redirect('livreur_mes_missions')


@login_required(login_url='/connexion/livreur/')
def livreur_profil(request):
    if request.user.role != 'livreur':
        return redirect('livreur_connexion')

    user = request.user
    from resto.models import LivreurProfile
    try:
        lp = user.livreur_profile
    except LivreurProfile.DoesNotExist:
        lp = LivreurProfile.objects.create(user=user, matricule_moto='')

    if request.method == 'POST':
        action = request.POST.get('action', 'profil')

        if action == 'profil':
            prenom    = request.POST.get('prenom', '').strip()
            nom       = request.POST.get('nom', '').strip()
            telephone = request.POST.get('telephone', '').strip()
            matricule = request.POST.get('matricule', '').strip()
            disponible   = request.POST.get('disponible') == '1'
            zone_radius  = request.POST.get('zone_radius', '8000').strip()
            photo_url    = request.POST.get('photo_url', '').strip()

            if not prenom or not nom:
                messages.error(request, "Prénom et nom sont obligatoires.")
            else:
                user.first_name = prenom
                user.last_name  = nom
                if telephone:
                    user.telephone = telephone
                user.save(update_fields=['first_name', 'last_name', 'telephone'])

                lp.matricule_moto = matricule
                lp.disponible     = disponible
                try:
                    lp.zone_radius = max(500, min(50000, int(zone_radius)))
                except (ValueError, TypeError):
                    pass
                if photo_url and not photo_url.startswith('data:') and len(photo_url) <= 2000:
                    lp.photo_url = photo_url
                lp.save()
                messages.success(request, "Profil mis à jour ✅")

        elif action == 'photo':
            avatar_file = request.FILES.get('avatar')
            if avatar_file:
                user.avatar = avatar_file
                user.save(update_fields=['avatar'])
                messages.success(request, "Photo de profil mise à jour ✅")
            else:
                messages.error(request, "Aucun fichier sélectionné.")

        elif action == 'password':
            old_pw  = request.POST.get('old_password', '')
            new_pw  = request.POST.get('new_password', '')
            new_pw2 = request.POST.get('new_password2', '')
            if not user.check_password(old_pw):
                messages.error(request, "Mot de passe actuel incorrect.")
            elif len(new_pw) < 6:
                messages.error(request, "Le nouveau mot de passe doit faire au moins 6 caractères.")
            elif new_pw != new_pw2:
                messages.error(request, "Les deux nouveaux mots de passe ne correspondent pas.")
            else:
                user.set_password(new_pw)
                user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                messages.success(request, "Mot de passe modifié ✅")

        return redirect('livreur_profil')

    total_missions   = user.missions_livraison.count()
    missions_livrees = user.missions_livraison.filter(statut='livree').count()
    missions_actives = user.missions_livraison.filter(
        statut__in=['accepte', 'en_recuperation', 'en_route']
    ).count()

    return render(request, 'livreur/profil.html', {
        'lp': lp,
        'total_missions':   total_missions,
        'missions_livrees': missions_livrees,
        'missions_actives': missions_actives,
    })


@login_required(login_url='/connexion/livreur/')
def livreur_reserver_web(request, order_id):
    if request.user.role != 'livreur':
        return redirect('livreur_connexion')

    from resto.models import Order
    from django.utils import timezone as tz
    from django.db import transaction

    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update(), id=order_id)

        if order.livreur is not None:
            messages.error(request, "Cette commande a déjà été réservée par un autre livreur.")
            return redirect('livreur_dashboard')
        if order.status != 'accepted':
            messages.error(request, "Cette commande n'est plus disponible.")
            return redirect('livreur_dashboard')

        order.livreur = request.user
        order.livreur_reserved_at = tz.now()
        order.status = 'in_progress'
        order.save(update_fields=['livreur', 'livreur_reserved_at', 'status'])

    try:
        profile = request.user.livreur_profile
        profile.disponible = False
        profile.save(update_fields=['disponible'])
    except Exception:
        pass

    from resto.services.fcm_service import send_push_notification
    if order.user and order.user.fcm_token:
        livreur_name = request.user.get_full_name() or request.user.username
        try:
            matricule = request.user.livreur_profile.matricule_moto
        except Exception:
            matricule = ""
        send_push_notification(
            fcm_token=order.user.fcm_token,
            title="🛵 Livreur assigné !",
            body=f"{livreur_name} ({matricule}) va livrer votre commande #{order.id}.",
            data={"order_id": str(order.id), "type": "livreur_assigned"},
        )

    messages.success(request, f"✅ Commande #{order.id} réservée avec succès !")
    return redirect('livreur_dashboard')


def livreur_deconnexion(request):
    logout(request)
    return redirect('livreur_connexion')


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


@api_view(["POST"])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_location(request):
    """Met à jour la position GPS de l'utilisateur connecté (client ou livreur)."""
    from django.contrib.gis.geos import Point
    from django.utils import timezone as tz

    try:
        lat = float(request.data.get('lat'))
        lng = float(request.data.get('lng'))
    except (TypeError, ValueError):
        return Response({"error": "lat et lng requis (nombres décimaux)."}, status=400)

    user = request.user
    pt = Point(lng, lat, srid=4326)
    user.last_lat = lat
    user.last_lng = lng
    user.last_location = pt
    user.location_updated_at = tz.now()
    user.save(update_fields=['last_lat', 'last_lng', 'last_location', 'location_updated_at'])

    # Enregistrer dans l'historique (max 50 points par utilisateur)
    from .models import UserPositionLog
    UserPositionLog.objects.create(user=user, lat=lat, lng=lng, position=pt)
    old_ids = list(
        UserPositionLog.objects.filter(user=user)
        .order_by('-recorded_at')
        .values_list('id', flat=True)[50:]
    )
    if old_ids:
        UserPositionLog.objects.filter(id__in=old_ids).delete()

    if user.role == 'livreur':
        try:
            from resto.models import LivreurProfile
            lp, _ = LivreurProfile.objects.get_or_create(user=user, defaults={"matricule_moto": "NC"})
            lp.latitude = lat
            lp.longitude = lng
            lp.location = pt
            lp.location_updated_at = tz.now()
            lp.save(update_fields=['latitude', 'longitude', 'location', 'location_updated_at'])
        except Exception:
            pass

    return Response({"status": "ok", "lat": lat, "lng": lng})


# ══════════════════════════════════════════════════════════════════════════════
# ESPACE VENDEUR
# ══════════════════════════════════════════════════════════════════════════════

from functools import wraps
from .models import VendeurProfile, Paiement
from .forms import (
    VendeurLoginForm, VendeurCreationForm, VendeurProfileForm,
    ProduitRestoForm, ProduitMarcheForm, ProduitShoppingForm,
    ProduitPerruqueForm, ProduitVoitureForm, ProduitImmobilierForm,
    ProduitQuicaillerieForm, BoutiqueForm,
)
from boutique.models import Boutique as _Boutique


def vendeur_required(view_func):
    """Décorateur : accès réservé aux vendeurs connectés (role='vendeur')."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('vendeur_connexion')
        if request.user.role != 'vendeur':
            messages.error(request, "Accès réservé aux vendeurs.")
            return redirect('vendeur_connexion')
        return view_func(request, *args, **kwargs)
    return _wrapped


# ── Connexion / Déconnexion ───────────────────────────────────────────────────

def vendeur_connexion(request):
    if request.user.is_authenticated and request.user.role == 'vendeur':
        return redirect('vendeur_dashboard')
    form = VendeurLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f"Bienvenue {user.first_name or user.telephone} 👋")
        return redirect('vendeur_dashboard')
    return render(request, 'vendeur/connexion.html', {'form': form})


def vendeur_deconnexion(request):
    logout(request)
    return redirect('vendeur_connexion')


# ── Helpers Boutique → Section ────────────────────────────────────────────────

_TYPE_TO_SECTION = {
    'marche':        'marche',
    'shopping':      'shopping',
    'quincaillerie': 'quicaillerie',
    'perruque':      'perruque',
    'voiture':       'voiture',
    'immobilier':    'immobilier',
    'restaurant':    'resto',
}


def _type_to_section(type_commerce):
    return _TYPE_TO_SECTION.get(type_commerce, '')


def _get_active_boutique(request):
    """Retourne la boutique active depuis la session, ou la première disponible."""
    boutiques = _Boutique.objects.filter(user=request.user).order_by('nom')
    bid = request.session.get('active_boutique_id')
    if bid:
        b = boutiques.filter(pk=bid).first()
        if b:
            return b
    first = boutiques.first()
    if first:
        request.session['active_boutique_id'] = first.pk
        request.session.modified = True
    return first


def _get_products_for_boutique(boutique):
    """Retourne les produits normalisés d'une boutique spécifique."""
    section = _type_to_section(boutique.type_commerce)
    try:
        if section == 'marche':
            from marche.models import Produit
            return _tag_section(list(Produit.objects.filter(vendeur=boutique).order_by('-date_creation')), 'marche')
        elif section == 'shopping':
            from shopping.models import Product
            return _tag_section(list(Product.objects.filter(shop=boutique).order_by('-created_at')), 'shopping')
        elif section == 'perruque':
            from perruque.models import WigProduct
            return _tag_section(list(WigProduct.objects.filter(shop=boutique).order_by('-created_at')), 'perruque')
        elif section == 'voiture':
            from voiture.models import Car
            return _tag_section(list(Car.objects.filter(shop=boutique).order_by('-created_at')), 'voiture')
        elif section == 'immobilier':
            from immobilier.models import Immobilier
            return _tag_section(list(Immobilier.objects.filter(vendeur__boutique=boutique).order_by('-date_creation')), 'immobilier')
        elif section == 'quicaillerie':
            from quicaillerie.models import ProduitQuincaillerie
            return _tag_section(list(ProduitQuincaillerie.objects.filter(boutique=boutique).order_by('-date_creation')), 'quicaillerie')
    except Exception:
        pass
    return []


@vendeur_required
def vendeur_switch_boutique(request, pk):
    """Change la boutique active en session et redirige vers la page précédente."""
    b = _Boutique.objects.filter(pk=pk, user=request.user).first()
    if b:
        request.session['active_boutique_id'] = b.pk
        request.session.modified = True
        messages.success(request, f"Boutique « {b.nom} » sélectionnée.")
    else:
        messages.error(request, "Boutique introuvable.")
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER', '/vendeur/dashboard/')
    return redirect(next_url)


def _boutiques_to_sections(boutiques):
    return list({
        _TYPE_TO_SECTION[b.type_commerce]
        for b in boutiques
        if b.type_commerce in _TYPE_TO_SECTION
    })


def _count_all_products(user):
    total = 0
    try:
        from shopping.models import Product
        total += Product.objects.filter(shop__user=user).count()
    except Exception:
        pass
    try:
        from perruque.models import WigProduct
        total += WigProduct.objects.filter(shop__user=user).count()
    except Exception:
        pass
    try:
        from voiture.models import Car
        total += Car.objects.filter(shop__user=user).count()
    except Exception:
        pass
    try:
        from immobilier.models import Immobilier
        total += Immobilier.objects.filter(vendeur__user=user).count()
    except Exception:
        pass
    try:
        from quicaillerie.models import ProduitQuincaillerie
        total += ProduitQuincaillerie.objects.filter(boutique__user=user).count()
    except Exception:
        pass
    try:
        from marche.models import Produit
        total += Produit.objects.filter(vendeur__user=user).count()
    except Exception:
        pass
    return total


def _get_all_reservations(user):
    reservations = []
    try:
        from voiture.models import Reservation
        reservations += list(Reservation.objects.filter(car__shop__user=user).order_by('-created_at')[:10])
    except Exception:
        pass
    try:
        from immobilier.models import DemandeVisite
        reservations += list(DemandeVisite.objects.filter(immobilier__vendeur__user=user).order_by('-created_at')[:10])
    except Exception:
        pass
    return reservations


def _normalize_product(p):
    """Ajoute des attributs d_* uniformes quel que soit le modèle produit."""
    # ── Nom ────────────────────────────────────────────────────────────────────
    brand = getattr(p, 'brand', None)
    if brand:
        p.d_nom = f"{brand} {getattr(p, 'model', '')} ({getattr(p, 'year', '')})"
    else:
        p.d_nom = '—'
        for field in ('title', 'name', 'nom', 'titre'):
            v = getattr(p, field, None)
            if v:
                p.d_nom = v
                break

    # ── Prix ───────────────────────────────────────────────────────────────────
    p.d_prix = 0
    for field in ('prix', 'price', 'base_price', 'daily_price'):
        v = getattr(p, field, None)
        if v is not None:
            p.d_prix = v
            break

    # ── Prix promo ─────────────────────────────────────────────────────────────
    p.d_promo = (getattr(p, 'prix_promo', None) or
                 getattr(p, 'promotional_price', None) or
                 getattr(p, 'prix_promotionnel', None))

    # ── Image URL ──────────────────────────────────────────────────────────────
    img = getattr(p, 'image', None)
    p.d_image = None
    if img:
        if hasattr(img, 'name') and img.name:   # ImageField (FieldFile)
            try:
                p.d_image = img.url
            except Exception:
                pass
        elif isinstance(img, str) and img:       # CharField (Dish.image = URL)
            p.d_image = img

    # ── Stock ──────────────────────────────────────────────────────────────────
    stock = getattr(p, 'stock', None)
    if stock is None:
        stock = getattr(p, 'quantite_stock', None)  # ProduitQuincaillerie
    p.d_stock = stock

    # ── Disponibilité ──────────────────────────────────────────────────────────
    status      = getattr(p, 'status', None)
    statut      = getattr(p, 'statut', None)
    active      = getattr(p, 'active', None)
    disponib    = getattr(p, 'disponibilite', None)

    if status is not None:
        p.d_disponible  = (status == 'available')
        p.d_statut_txt  = p.get_status_display() if hasattr(p, 'get_status_display') else status
    elif statut is not None:
        p.d_disponible  = (statut == 'disponible')
        p.d_statut_txt  = p.get_statut_display() if hasattr(p, 'get_statut_display') else statut
    elif active is not None:
        p.d_disponible  = bool(active)
        p.d_statut_txt  = 'Actif' if active else 'Inactif'
    elif disponib is not None:
        p.d_disponible  = bool(disponib)
        p.d_statut_txt  = 'Disponible' if disponib else 'Indisponible'
    else:
        p.d_disponible  = True
        p.d_statut_txt  = None

    # ── Date ───────────────────────────────────────────────────────────────────
    p.d_date = getattr(p, 'created_at', None) or getattr(p, 'date_creation', None)

    return p


def _tag_section(products, section):
    """Tag each product with its section name and normalized display attributes."""
    for p in products:
        p.vendeur_section = section
        _normalize_product(p)
    return products


def _get_all_products(user):
    items = []
    try:
        from resto.models import Dish, Restaurant
        restaurants = Restaurant.objects.filter(proprietaire=user)
        items += _tag_section(list(Dish.objects.filter(restaurant__in=restaurants).order_by('-created_at')), 'resto')
    except Exception:
        pass
    try:
        from marche.models import Produit
        items += _tag_section(list(Produit.objects.filter(vendeur__user=user).order_by('-date_creation')), 'marche')
    except Exception:
        pass
    try:
        from shopping.models import Product
        items += _tag_section(list(Product.objects.filter(shop__user=user).order_by('-created_at')), 'shopping')
    except Exception:
        pass
    try:
        from perruque.models import WigProduct
        items += _tag_section(list(WigProduct.objects.filter(shop__user=user).order_by('-created_at')), 'perruque')
    except Exception:
        pass
    try:
        from voiture.models import Car
        items += _tag_section(list(Car.objects.filter(shop__user=user).order_by('-created_at')), 'voiture')
    except Exception:
        pass
    try:
        from immobilier.models import Immobilier
        items += _tag_section(list(Immobilier.objects.filter(vendeur__user=user).order_by('-date_creation')), 'immobilier')
    except Exception:
        pass
    try:
        from quicaillerie.models import ProduitQuincaillerie
        items += _tag_section(list(ProduitQuincaillerie.objects.filter(boutique__user=user).order_by('-date_creation')), 'quicaillerie')
    except Exception:
        pass
    return items


# ── Dashboard ─────────────────────────────────────────────────────────────────

@vendeur_required
def vendeur_dashboard(request):
    vp = getattr(request.user, 'vendeur_profile', None)
    boutiques = _Boutique.objects.filter(user=request.user)

    nb_produits = _count_all_products(request.user)
    reservations = _get_all_reservations(request.user)

    # Commandes resto
    nb_commandes = 0
    commandes_recentes = []
    try:
        from resto.models import Order, Restaurant
        restaurants = Restaurant.objects.filter(proprietaire=request.user)
        if restaurants.exists():
            dish_ids = []
            for r in restaurants:
                dish_ids += list(r.dishes.values_list('id', flat=True))
            commandes_qs = Order.objects.filter(items__dish_id__in=dish_ids).distinct().order_by('-created_at')
            nb_commandes = commandes_qs.filter(status__in=['pending', 'accepted', 'in_progress']).count()
            commandes_recentes = list(commandes_qs[:5])
    except Exception:
        pass

    sections = _boutiques_to_sections(boutiques)
    paiements_recents = []
    if sections:
        paiements_recents = list(Paiement.objects.filter(section__in=sections).order_by('-cree_le')[:5])

    return render(request, 'vendeur/dashboard.html', {
        'vp': vp,
        'boutiques': boutiques,
        'nb_produits': nb_produits,
        'nb_reservations': len(reservations),
        'reservations_recentes': reservations[:5],
        'nb_commandes': nb_commandes,
        'commandes_recentes': commandes_recentes,
        'paiements_recents': paiements_recents,
    })


# ── Commandes ─────────────────────────────────────────────────────────────────

@vendeur_required
def vendeur_commandes(request):
    vp = getattr(request.user, 'vendeur_profile', None)
    user = request.user

    boutiques = _Boutique.objects.filter(user=user)
    sections = _boutiques_to_sections(boutiques)
    if vp and vp.section and vp.section not in sections:
        sections.append(vp.section)

    # Paiements pour toutes les sections du vendeur (marché, shopping, perruque, quicaillerie, etc.)
    paiements_qs = (
        Paiement.objects.filter(section__in=sections).select_related('client').order_by('-cree_le')
        if sections else Paiement.objects.none()
    )

    # Commandes resto (Order), voiture (Reservation), immobilier (DemandeVisite)
    autres_commandes = []
    try:
        from resto.models import Order, Restaurant
        restaurants = Restaurant.objects.filter(proprietaire=user)
        if restaurants.exists():
            dish_ids = []
            for r in restaurants:
                dish_ids += list(r.dishes.values_list('id', flat=True))
            autres_commandes += list(Order.objects.filter(items__dish_id__in=dish_ids).distinct().order_by('-created_at'))
    except Exception:
        pass

    try:
        from voiture.models import Reservation
        autres_commandes += list(Reservation.objects.filter(car__shop__user=user).order_by('-created_at'))
    except Exception:
        pass

    try:
        from immobilier.models import DemandeVisite
        autres_commandes += list(DemandeVisite.objects.filter(immobilier__vendeur__user=user).order_by('-created_at'))
    except Exception:
        pass

    statut_filter = request.GET.get('statut', '')
    if statut_filter:
        paiements_qs = paiements_qs.filter(statut=statut_filter)
        autres_commandes = [c for c in autres_commandes if getattr(c, 'status', getattr(c, 'statut', '')) == statut_filter]

    from django.core.paginator import Paginator
    primary_section = vp.section if vp else (sections[0] if sections else '')

    paginator = Paginator(paiements_qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'vendeur/commandes.html', {
        'vp': vp,
        'section': primary_section,
        'commandes': autres_commandes,
        'paiements': page_obj,   # garder 'paiements' pour le JS seenIds existant
        'page_obj': page_obj,
        'statut_filter': statut_filter,
    })


# ── Boutiques ─────────────────────────────────────────────────────────────────

@vendeur_required
def vendeur_boutiques(request):
    return redirect('vendeur_mes_boutiques')


# ── Produits ──────────────────────────────────────────────────────────────────

@vendeur_required
def vendeur_produits(request):
    from django.core.paginator import Paginator
    vp = getattr(request.user, 'vendeur_profile', None)
    active_boutique = _get_active_boutique(request)
    toutes = request.GET.get('toutes') == '1'

    if active_boutique and not toutes:
        produits = _get_products_for_boutique(active_boutique)
    else:
        produits = _get_all_products(request.user)

    paginator = Paginator(produits, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'vendeur/produits/liste.html', {
        'vp': vp,
        'page_obj': page_obj,
        'toutes': toutes,
        'active_boutique': active_boutique,
    })


# ── Ajouter un produit ────────────────────────────────────────────────────────

_FORM_MAP = {
    'resto':        ProduitRestoForm,
    'marche':       ProduitMarcheForm,
    'shopping':     ProduitShoppingForm,
    'perruque':     ProduitPerruqueForm,
    'voiture':      ProduitVoitureForm,
    'immobilier':   ProduitImmobilierForm,
    'quicaillerie': ProduitQuicaillerieForm,
}


@vendeur_required
def vendeur_ajouter_produit(request):
    vp = getattr(request.user, 'vendeur_profile', None)

    # Déterminer la boutique : URL param > session active > première disponible
    section = vp.section if vp else None
    boutique = None
    boutique_id = request.GET.get('boutique') or request.POST.get('boutique')
    if boutique_id:
        boutique = _Boutique.objects.filter(pk=boutique_id, user=request.user).first()
        if boutique:
            section = _type_to_section(boutique.type_commerce) or section
    if not boutique:
        boutique = _get_active_boutique(request)
        if boutique and not section:
            section = _type_to_section(boutique.type_commerce)

    FormCls = _FORM_MAP.get(section)
    if FormCls is None:
        messages.error(request, "Créez d'abord une boutique pour pouvoir ajouter des produits.")
        return redirect('boutique:vendeur_mes_boutiques')

    # Si l'admin accède à cette vue, il peut choisir n'importe quelle boutique
    is_admin = request.user.role == 'admin'
    all_boutiques = _Boutique.objects.filter(user=request.user) if not is_admin else _Boutique.objects.select_related('user').all()

    if request.method == 'POST':
        form = FormCls(request.POST, request.FILES)
        # Admin : boutique sélectionnée depuis le POST
        if is_admin and not boutique:
            admin_b_id = request.POST.get('boutique_admin')
            if admin_b_id:
                boutique = _Boutique.objects.filter(pk=admin_b_id).first()
                if boutique and not section:
                    section = _type_to_section(boutique.type_commerce)
        if form.is_valid():
            try:
                produit = _save_produit(form, section, boutique, request.user)
                messages.success(request, "Produit créé ✅  Ajoutez maintenant des photos.")
                pk = str(produit.pk)
                return redirect('vendeur_images_produit', section=section, pk=pk)
            except Exception as e:
                messages.error(request, f"Erreur lors de l'enregistrement : {e}")
    else:
        form = FormCls()

    return render(request, 'vendeur/produits/form.html', {
        'vp': vp, 'form': form, 'mode': 'ajouter',
        'boutique': boutique, 'section': section,
        'is_admin': is_admin,
        'all_boutiques': all_boutiques if is_admin else None,
    })


def _save_produit(form, section, boutique, user):
    """Enregistre le produit et retourne l'objet créé."""
    if section == 'resto':
        from resto.models import Restaurant
        restaurant = Restaurant.objects.filter(proprietaire=user).first()
        if not restaurant:
            raise ValueError("Aucun restaurant lié à ce compte.")
        return form.save_for_restaurant(restaurant)
    elif section == 'marche':
        if not boutique:
            raise ValueError("Aucun stand/boutique marché lié à ce compte.")
        return form.save_for_vendeur(boutique)
    else:
        if not boutique:
            raise ValueError("Créez d'abord une boutique.")
        return form.save_for_shop(boutique)


# ── Helpers images ─────────────────────────────────────────────────────────────

def _get_product_images(section, pk, user):
    """Retourne (produit, queryset_images) ou (None, None) si introuvable/non autorisé."""
    try:
        if section == 'marche':
            from marche.models import Produit, ProduitImage
            p = Produit.objects.filter(pk=pk, vendeur__user=user).first()
            return p, (p.images.all() if p else None)
        elif section == 'shopping':
            from shopping.models import Product, ProductImage
            p = Product.objects.filter(pk=pk, shop__user=user).first()
            return p, (p.images.all() if p else None)
        elif section == 'perruque':
            from perruque.models import WigProduct, ProductImage
            p = WigProduct.objects.filter(pk=pk, shop__user=user).first()
            return p, (p.images.all() if p else None)
        elif section == 'voiture':
            from voiture.models import Car, CarImage
            p = Car.objects.filter(pk=pk, shop__user=user).first()
            return p, (p.images.all() if p else None)
        elif section == 'immobilier':
            from immobilier.models import Immobilier, PhotoImmobilier
            p = Immobilier.objects.filter(pk=pk, vendeur__user=user).first()
            return p, (p.photos.all() if p else None)
        elif section == 'quicaillerie':
            from quicaillerie.models import ProduitQuincaillerie, ProductImage
            p = ProduitQuincaillerie.objects.filter(pk=pk, boutique__user=user).first()
            return p, (p.images.all() if p else None)
        elif section == 'resto':
            from resto.models import Dish, Restaurant
            rests = Restaurant.objects.filter(proprietaire=user)
            p = Dish.objects.filter(pk=pk, restaurant__in=rests).first()
            return p, None   # Dish n'a pas de modèle image séparé
    except Exception:
        pass
    return None, None


def _get_image_meta(section):
    """Retourne (couleurs_qs, tailles_qs) disponibles pour la section, ou (None, None)."""
    if section in ('shopping', 'perruque', 'quicaillerie'):
        from shopping.models import Couleur, Taille
        return Couleur.objects.all(), Taille.objects.all()
    if section == 'marche':
        from marche.models import Couleur
        return Couleur.objects.all(), None
    return None, None


def _add_product_image(section, pk, user, post, files):
    """Crée une image liée au produit — sauvegarde couleur, tailles, ordre, description."""
    image_file = files.get('image')
    if not image_file:
        return
    principale  = bool(post.get('principale'))
    ordre       = int(post.get('ordre', 0) or 0)
    description = post.get('description', '')
    couleur_id  = post.get('couleur') or None
    tailles_ids = post.getlist('tailles')

    if section == 'marche':
        from marche.models import Produit, ProduitImage, Couleur
        p = Produit.objects.filter(pk=pk, vendeur__user=user).first()
        if p:
            couleur = Couleur.objects.filter(pk=couleur_id).first() if couleur_id else None
            ProduitImage.objects.create(
                produit=p, image=image_file, principale=principale,
                ordre=ordre, description=description, couleur=couleur,
            )
    elif section == 'shopping':
        from shopping.models import Product, ProductImage, Couleur, Taille
        p = Product.objects.filter(pk=pk, shop__user=user).first()
        if p:
            couleur = Couleur.objects.filter(pk=couleur_id).first() if couleur_id else None
            img = ProductImage.objects.create(
                product=p, image=image_file, principale=principale,
                ordre=ordre, description=description, couleur=couleur,
            )
            if tailles_ids:
                img.tailles.set(Taille.objects.filter(pk__in=tailles_ids))
    elif section == 'perruque':
        from perruque.models import WigProduct, ProductImage
        from shopping.models import Couleur, Taille
        p = WigProduct.objects.filter(pk=pk, shop__user=user).first()
        if p:
            couleur = Couleur.objects.filter(pk=couleur_id).first() if couleur_id else None
            img = ProductImage.objects.create(
                product=p, image=image_file, principale=principale,
                ordre=ordre, description=description, couleur=couleur,
            )
            if tailles_ids:
                img.tailles.set(Taille.objects.filter(pk__in=tailles_ids))
    elif section == 'voiture':
        from voiture.models import Car, CarImage
        p = Car.objects.filter(pk=pk, shop__user=user).first()
        if p:
            CarImage.objects.create(car=p, image=image_file, principale=principale, ordre=ordre)
    elif section == 'immobilier':
        from immobilier.models import Immobilier, PhotoImmobilier
        p = Immobilier.objects.filter(pk=pk, vendeur__user=user).first()
        if p:
            PhotoImmobilier.objects.create(bien=p, image=image_file, principale=principale, ordre=ordre)
    elif section == 'quicaillerie':
        from quicaillerie.models import ProduitQuincaillerie, ProductImage
        from shopping.models import Couleur, Taille
        p = ProduitQuincaillerie.objects.filter(pk=pk, boutique__user=user).first()
        if p:
            couleur = Couleur.objects.filter(pk=couleur_id).first() if couleur_id else None
            img = ProductImage.objects.create(
                produit=p, image=image_file, principale=principale,
                ordre=ordre, description=description, couleur=couleur,
            )
            if tailles_ids:
                img.tailles.set(Taille.objects.filter(pk__in=tailles_ids))


@vendeur_required
def vendeur_images_produit(request, section, pk):
    """Page d'ajout de photos supplémentaires après création (ou modification) d'un produit."""
    vp = getattr(request.user, 'vendeur_profile', None)

    produit, images = _get_product_images(section, pk, request.user)
    if produit is None:
        messages.error(request, "Produit introuvable.")
        return redirect('vendeur_produits')

    couleurs, tailles = _get_image_meta(section)

    if request.method == 'POST':
        if 'image' in request.FILES:
            _add_product_image(section, pk, request.user, request.POST, request.FILES)
            messages.success(request, "Photo ajoutée ✅")
        return redirect('vendeur_images_produit', section=section, pk=pk)

    return render(request, 'vendeur/produits/images.html', {
        'vp': vp, 'section': section, 'pk': pk,
        'produit': produit, 'images': images,
        'couleurs': couleurs, 'tailles': tailles,
    })


def _build_initial(section, p):
    """Construit le dict initial pour pré-remplir le formulaire depuis une instance produit."""
    if section == 'marche':
        return {
            'nom': getattr(p, 'nom', ''), 'categorie': getattr(p, 'categorie_id', None),
            'marche': getattr(p, 'marche_id', None), 'description': getattr(p, 'description', ''),
            'prix': getattr(p, 'prix', 0), 'prix_promo': getattr(p, 'prix_promo', None),
            'promo_debut': getattr(p, 'promo_debut', None), 'promo_fin': getattr(p, 'promo_fin', None),
            'unite': getattr(p, 'unite', 'pièce'), 'stock': getattr(p, 'stock', 0),
            'disponibilite': getattr(p, 'disponibilite', True),
        }
    elif section == 'shopping':
        return {
            'name': getattr(p, 'name', ''), 'category': getattr(p, 'category_id', None),
            'description': getattr(p, 'description', ''), 'price': getattr(p, 'price', 0),
            'prix_promo': getattr(p, 'prix_promo', None), 'promo_debut': getattr(p, 'promo_debut', None),
            'promo_fin': getattr(p, 'promo_fin', None), 'stock': getattr(p, 'stock', 0),
            'active': getattr(p, 'active', True),
        }
    elif section == 'perruque':
        return {
            'name': getattr(p, 'name', ''), 'category': getattr(p, 'category_id', None),
            'description': getattr(p, 'description', ''), 'price': getattr(p, 'price', 0),
            'promotional_price': getattr(p, 'promotional_price', None),
            'promo_debut': getattr(p, 'promo_debut', None), 'promo_fin': getattr(p, 'promo_fin', None),
            'material': getattr(p, 'material', 'synthetic'), 'texture': getattr(p, 'texture', 'straight'),
            'color': getattr(p, 'color', ''), 'length': getattr(p, 'length', ''),
            'stock': getattr(p, 'stock', 0), 'status': getattr(p, 'status', 'available'),
            'city': getattr(p, 'city', ''), 'location': getattr(p, 'location', ''),
            'delivery_available': getattr(p, 'delivery_available', True),
        }
    elif section == 'voiture':
        return {
            'brand': getattr(p, 'brand', ''), 'model': getattr(p, 'model', ''),
            'year': getattr(p, 'year', 2020), 'color': getattr(p, 'color', ''),
            'category': getattr(p, 'category_id', None), 'daily_price': getattr(p, 'daily_price', 0),
            'promotional_price': getattr(p, 'promotional_price', None),
            'promo_debut': getattr(p, 'promo_debut', None), 'promo_fin': getattr(p, 'promo_fin', None),
            'deposit': getattr(p, 'deposit', 0), 'seats': getattr(p, 'seats', 5),
            'doors': getattr(p, 'doors', 4), 'transmission': getattr(p, 'transmission', 'manual'),
            'fuel': getattr(p, 'fuel', 'gasoline'),
            'air_conditioning': getattr(p, 'air_conditioning', False),
            'driver_included': getattr(p, 'driver_included', False),
            'city': getattr(p, 'city', ''), 'location': getattr(p, 'location', ''),
            'description': getattr(p, 'description', ''),
        }
    elif section == 'immobilier':
        return {
            'titre': getattr(p, 'titre', ''), 'type_bien': getattr(p, 'type_bien', 'maison'),
            'type_offre': getattr(p, 'type_offre', 'vente'), 'categorie': getattr(p, 'categorie_id', None),
            'prix': getattr(p, 'prix', 0), 'prix_promo': getattr(p, 'prix_promotionnel', None),
            'superficie': getattr(p, 'superficie', None),
            'nombre_chambres': getattr(p, 'nombre_chambres', 0),
            'nombre_salles_bain': getattr(p, 'nombre_salles_bain', 0),
            'nombre_salons': getattr(p, 'nombre_salons', 0),
            'nombre_cuisines': getattr(p, 'nombre_cuisines', 0),
            'nombre_garages': getattr(p, 'nombre_garages', 0),
            'description': getattr(p, 'description', ''),
            'adresse': getattr(p, 'adresse', ''),
            'meuble': getattr(p, 'meuble', False), 'piscine': getattr(p, 'piscine', False),
            'parking': getattr(p, 'parking', False), 'climatisation': getattr(p, 'climatisation', False),
            'gardiennage': getattr(p, 'gardien', getattr(p, 'gardiennage', False)),
        }
    elif section == 'quicaillerie':
        return {
            'nom': getattr(p, 'nom', ''), 'categorie': getattr(p, 'categorie_id', None),
            'reference': getattr(p, 'reference', ''), 'marque': getattr(p, 'marque', ''),
            'description': getattr(p, 'description', ''), 'prix': getattr(p, 'prix', 0),
            'prix_promotionnel': getattr(p, 'prix_promotionnel', None),
            'quantite_stock': getattr(p, 'quantite_stock', 0),
            'unite': getattr(p, 'unite', 'Pièce'), 'etat': getattr(p, 'etat', 'neuf'),
            'statut': getattr(p, 'statut', 'disponible'), 'garantie': getattr(p, 'garantie', ''),
            'ville': getattr(p, 'ville', ''), 'adresse': getattr(p, 'adresse', ''),
            'livraison_disponible': getattr(p, 'livraison_disponible', True),
        }
    elif section == 'resto':
        return {
            'title': getattr(p, 'title', ''), 'description': getattr(p, 'description', ''),
            'base_price': getattr(p, 'base_price', 0),
            'base_time_minutes': getattr(p, 'base_time_minutes', 20),
            'image': getattr(p, 'image', ''), 'active': getattr(p, 'active', True),
        }
    return {}


def _update_produit(section, pk, user, cd):
    """Met à jour un produit existant depuis form.cleaned_data. Retourne l'instance ou None."""
    if section == 'marche':
        from marche.models import Produit
        p = Produit.objects.filter(pk=pk, vendeur__user=user).first()
        if p:
            p.nom = cd['nom']; p.categorie = cd.get('categorie'); p.marche = cd.get('marche')
            p.description = cd.get('description', ''); p.prix = cd['prix']
            p.prix_promo = cd.get('prix_promo'); p.promo_debut = cd.get('promo_debut')
            p.promo_fin = cd.get('promo_fin')
            p.unite = cd.get('unite', 'pièce') or 'pièce'; p.stock = cd.get('stock', 0)
            p.disponibilite = cd.get('disponibilite', True)
            if cd.get('image'): p.image = cd['image']
            p.save(); return p
    elif section == 'shopping':
        from shopping.models import Product
        p = Product.objects.filter(pk=pk, shop__user=user).first()
        if p:
            p.name = cd['name']; p.category = cd.get('category')
            p.description = cd['description']; p.price = cd['price']
            p.prix_promo = cd.get('prix_promo'); p.promo_debut = cd.get('promo_debut')
            p.promo_fin = cd.get('promo_fin'); p.stock = cd['stock']
            p.active = cd.get('active', True); p.save(); return p
    elif section == 'perruque':
        from perruque.models import WigProduct
        p = WigProduct.objects.filter(pk=pk, shop__user=user).first()
        if p:
            p.name = cd['name']; p.category = cd.get('category')
            p.description = cd.get('description', ''); p.price = cd['price']
            p.promotional_price = cd.get('promotional_price')
            p.promo_debut = cd.get('promo_debut'); p.promo_fin = cd.get('promo_fin')
            p.material = cd['material']; p.texture = cd['texture']
            p.color = cd.get('color', ''); p.length = cd.get('length', '')
            p.stock = cd.get('stock', 0); p.status = cd.get('status', 'available')
            p.city = cd.get('city', ''); p.location = cd.get('location', '')
            p.delivery_available = cd.get('delivery_available', True)
            p.save(); return p
    elif section == 'voiture':
        from voiture.models import Car
        p = Car.objects.filter(pk=pk, shop__user=user).first()
        if p:
            p.brand = cd['brand']; p.model = cd['model']; p.year = cd['year']
            p.color = cd.get('color', ''); p.category = cd.get('category')
            p.daily_price = cd['daily_price']; p.promotional_price = cd.get('promotional_price')
            p.promo_debut = cd.get('promo_debut'); p.promo_fin = cd.get('promo_fin')
            p.deposit = cd.get('deposit') or 0; p.seats = cd.get('seats', 5)
            p.doors = cd.get('doors', 4) or 4; p.transmission = cd['transmission']
            p.fuel = cd['fuel']; p.air_conditioning = cd.get('air_conditioning', False)
            p.driver_included = cd.get('driver_included', False)
            p.city = cd.get('city', ''); p.location = cd.get('location', '')
            p.description = cd.get('description', ''); p.save(); return p
    elif section == 'immobilier':
        from immobilier.models import Immobilier
        p = Immobilier.objects.filter(pk=pk, vendeur__user=user).first()
        if p:
            p.titre = cd['titre']; p.type_bien = cd['type_bien']; p.type_offre = cd['type_offre']
            p.categorie = cd.get('categorie'); p.prix = cd['prix']
            p.prix_promotionnel = cd.get('prix_promo'); p.superficie = cd.get('superficie')
            p.nombre_chambres = cd.get('nombre_chambres', 0) or 0
            p.nombre_salles_bain = cd.get('nombre_salles_bain', 0) or 0
            p.nombre_salons = cd.get('nombre_salons', 0) or 0
            p.nombre_cuisines = cd.get('nombre_cuisines', 0) or 0
            p.nombre_garages = cd.get('nombre_garages', 0) or 0
            p.description = cd.get('description', '')
            p.meuble = cd.get('meuble', False); p.piscine = cd.get('piscine', False)
            p.parking = cd.get('parking', False); p.climatisation = cd.get('climatisation', False)
            if hasattr(p, 'gardien'): p.gardien = cd.get('gardiennage', False)
            p.save(); return p
    elif section == 'quicaillerie':
        from quicaillerie.models import ProduitQuincaillerie
        p = ProduitQuincaillerie.objects.filter(pk=pk, boutique__user=user).first()
        if p:
            p.nom = cd['nom']; p.categorie = cd.get('categorie')
            p.reference = cd.get('reference', ''); p.marque = cd.get('marque', '')
            p.description = cd.get('description', ''); p.prix = cd['prix']
            p.prix_promotionnel = cd.get('prix_promotionnel')
            p.quantite_stock = cd.get('quantite_stock', 0)
            p.unite = cd.get('unite', 'Pièce') or 'Pièce'
            p.etat = cd.get('etat', 'neuf'); p.statut = cd.get('statut', 'disponible')
            p.garantie = cd.get('garantie', ''); p.ville = cd.get('ville', '')
            p.adresse = cd.get('adresse', '')
            p.livraison_disponible = cd.get('livraison_disponible', True)
            p.save(); return p
    elif section == 'resto':
        from resto.models import Dish, Restaurant
        rests = Restaurant.objects.filter(proprietaire=user)
        p = Dish.objects.filter(pk=pk, restaurant__in=rests).first()
        if p:
            p.title = cd['title']; p.description = cd.get('description', '')
            p.base_price = cd['base_price']; p.base_time_minutes = cd['base_time_minutes']
            if cd.get('image'): p.image = cd['image']
            p.active = cd.get('active', True); p.save(); return p
    return None


@vendeur_required
def vendeur_detail_produit(request, section, pk):
    """Fiche détaillée d'un produit vendeur (lecture seule)."""
    vp = getattr(request.user, 'vendeur_profile', None)
    produit, images = _get_product_images(section, pk, request.user)
    if produit is None:
        messages.error(request, "Produit introuvable.")
        return redirect('vendeur_produits')
    _normalize_product(produit)
    return render(request, 'vendeur/produits/detail.html', {
        'vp': vp, 'section': section, 'pk': pk,
        'produit': produit, 'images': images,
    })


@vendeur_required
def vendeur_modifier_produit(request, section, pk):
    """Modifier un produit existant."""
    vp = getattr(request.user, 'vendeur_profile', None)
    produit, images = _get_product_images(section, pk, request.user)
    if produit is None:
        messages.error(request, "Produit introuvable.")
        return redirect('vendeur_produits')

    FormCls = _FORM_MAP.get(section)
    if FormCls is None:
        return redirect('vendeur_produits')

    if request.method == 'POST':
        form = FormCls(request.POST, request.FILES)
        if form.is_valid():
            updated = _update_produit(section, pk, request.user, form.cleaned_data)
            if updated:
                messages.success(request, "Produit modifié avec succès ✅")
                return redirect('vendeur_detail_produit', section=section, pk=pk)
            messages.error(request, "Impossible de modifier ce produit.")
    else:
        _normalize_product(produit)
        form = FormCls(initial=_build_initial(section, produit))

    boutique = (getattr(produit, 'vendeur', None) or getattr(produit, 'shop', None)
                or getattr(produit, 'boutique', None))
    return render(request, 'vendeur/produits/form.html', {
        'vp': vp, 'section': section, 'pk': pk,
        'form': form, 'boutique': boutique,
        'is_modifier': True, 'produit': produit,
        'is_admin': False, 'all_boutiques': None,
    })


@vendeur_required
def vendeur_supprimer_produit(request, section, pk):
    """Suppression d'un produit selon sa section."""
    try:
        _delete_produit(section, pk, request.user)
        messages.success(request, "Produit supprimé.")
    except Exception as e:
        messages.error(request, f"Erreur : {e}")
    return redirect('vendeur_produits')


def _delete_produit(section, pk, user):
    if section == 'resto':
        from resto.models import Dish, Restaurant
        restaurants = Restaurant.objects.filter(proprietaire=user)
        Dish.objects.filter(pk=pk, restaurant__in=restaurants).delete()
    elif section == 'marche':
        from marche.models import Produit
        Produit.objects.filter(pk=pk, vendeur__user=user).delete()
    elif section == 'shopping':
        from shopping.models import Product
        Product.objects.filter(pk=pk, shop__user=user).delete()
    elif section == 'perruque':
        from perruque.models import WigProduct
        WigProduct.objects.filter(pk=pk, shop__user=user).delete()
    elif section == 'voiture':
        from voiture.models import Car
        Car.objects.filter(pk=pk, shop__user=user).delete()
    elif section == 'immobilier':
        from immobilier.models import Immobilier
        Immobilier.objects.filter(pk=pk, vendeur__user=user).delete()
    elif section == 'quicaillerie':
        from quicaillerie.models import ProduitQuincaillerie
        ProduitQuincaillerie.objects.filter(pk=pk, boutique__user=user).delete()


# ── Profil vendeur ────────────────────────────────────────────────────────────

@vendeur_required
def vendeur_profil(request):
    from django.contrib.auth import update_session_auth_hash
    user = request.user
    vp = getattr(user, 'vendeur_profile', None)

    if request.method == 'POST' and vp:
        action = request.POST.get('action', 'profil')

        if action == 'profil':
            user.first_name = request.POST.get('prenom', user.first_name).strip()
            user.last_name  = request.POST.get('nom', user.last_name).strip()
            telephone = request.POST.get('telephone', '').strip()
            if telephone:
                user.telephone = telephone
            user.save(update_fields=['first_name', 'last_name', 'telephone'])

            vp.nom_commercial = request.POST.get('nom_commercial', vp.nom_commercial).strip()
            vp.description    = request.POST.get('description', vp.description).strip()
            vp.telephone_pro  = request.POST.get('telephone_pro', vp.telephone_pro).strip()
            vp.email_pro      = request.POST.get('email_pro', vp.email_pro).strip()
            vp.site_web       = request.POST.get('site_web', vp.site_web).strip()
            vp.save(update_fields=['nom_commercial', 'description', 'telephone_pro', 'email_pro', 'site_web'])
            messages.success(request, "Informations mises à jour ✅")

        elif action == 'logo':
            logo_file = request.FILES.get('logo')
            if logo_file:
                vp.logo = logo_file
                vp.save(update_fields=['logo'])
                messages.success(request, "Logo mis à jour ✅")
            else:
                messages.error(request, "Aucun fichier sélectionné.")

        elif action == 'password':
            old_pw  = request.POST.get('old_password', '')
            new_pw  = request.POST.get('new_password', '')
            new_pw2 = request.POST.get('new_password2', '')
            if not user.check_password(old_pw):
                messages.error(request, "Mot de passe actuel incorrect.")
            elif len(new_pw) < 6:
                messages.error(request, "Le nouveau mot de passe doit faire au moins 6 caractères.")
            elif new_pw != new_pw2:
                messages.error(request, "Les mots de passe ne correspondent pas.")
            else:
                user.set_password(new_pw)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Mot de passe modifié ✅")

        return redirect('vendeur_profil')

    return render(request, 'vendeur/profil.html', {'vp': vp})


# ── Paiements ─────────────────────────────────────────────────────────────────

@vendeur_required
def vendeur_paiements(request):
    from django.core.paginator import Paginator
    vp = getattr(request.user, 'vendeur_profile', None)
    boutiques = _Boutique.objects.filter(user=request.user)
    sections = _boutiques_to_sections(boutiques)
    if vp and vp.section and vp.section not in sections:
        sections.append(vp.section)

    paiements = (
        Paiement.objects.filter(section__in=sections).order_by('-cree_le')
        if sections else Paiement.objects.none()
    )
    statut = request.GET.get('statut', '')
    if statut:
        paiements = paiements.filter(statut=statut)

    paginator = Paginator(paiements, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'vendeur/paiements/liste.html', {
        'vp': vp,
        'page_obj': page_obj,
        'statut_filter': statut,
        'statuts': Paiement.STATUTS,
    })


@vendeur_required
def vendeur_paiement_detail(request, pk):
    vp = getattr(request.user, 'vendeur_profile', None)
    boutiques = _Boutique.objects.filter(user=request.user)
    sections = _boutiques_to_sections(boutiques)
    if vp and vp.section and vp.section not in sections:
        sections.append(vp.section)
    if sections:
        paiement = get_object_or_404(Paiement, pk=pk, section__in=sections)
    else:
        messages.error(request, "Paiement introuvable.")
        return redirect('vendeur_paiements')
    try:
        cart_items = _sanitize_cart_items(_json.loads(paiement.notes) if paiement.notes else [])
    except Exception:
        cart_items = []

    try:
        livraison = paiement.livraison
    except Exception:
        livraison = None

    return render(request, 'vendeur/paiements/detail.html', {
        'vp': vp,
        'paiement': paiement,
        'cart_items': cart_items,
        'livraison': livraison,
    })


# ── Admin : créer un compte vendeur ──────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def admin_creer_vendeur(request):
    form = VendeurCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        messages.success(request, f"Compte vendeur créé pour {user.first_name} ({user.telephone}) ✅")
        return redirect('admin_panel_vendeurs')
    return render(request, 'admin_panel/creer_vendeur.html', {'form': form})


# ═══════════════════════════════════════════════════════════════════════════════
# PAIEMENT — Checkout, confirmation
# ═══════════════════════════════════════════════════════════════════════════════

import json as _json
from decimal import Decimal


def _sanitize_cart_image(url):
    """
    Normalise l'URL d'image d'un article de panier.
    - URL absolue (http://ngrok…, http://127.0.0.1…) → extrait le path seul (/media/…)
    - URL vide / invalide → chaîne vide
    """
    if not url or not isinstance(url, str):
        return ''
    url = url.strip()
    if not url:
        return ''
    if url.startswith('/'):
        return url  # déjà relatif, OK
    from urllib.parse import urlparse
    try:
        path = urlparse(url).path
        return path if path else ''
    except Exception:
        return ''


def _sanitize_cart_items(items):
    """Corrige les URLs image de chaque item du panier."""
    for item in items:
        if isinstance(item, dict):
            item['image'] = _sanitize_cart_image(item.get('image', ''))
    return items


QUARTIERS_BZV = [
    'Bacongo', 'Makélékélé', 'Moungali', 'Ouenzé', 'Talangaï',
    'Mfilou', 'Djiri', 'Madibou', 'Poto-Poto', 'Plateau',
    'Centre-ville', 'Autre',
]

SECTION_LABELS = {
    'marche':       'Marché',
    'quicaillerie': 'Quincaillerie',
    'shopping':     'Shopping',
    'perruque':     'Perruque & Beauté',
    'voiture':      'Location Voiture',
    'immobilier':   'Immobilier',
    'resto':        'Restaurant',
}


def paiement_checkout(request):
    """Reçoit le panier (JSON POST) et affiche la page de paiement."""
    if not request.user.is_authenticated:
        from urllib.parse import urlencode
        return redirect('/connexion/?' + urlencode({'next': '/paiement/'}))

    if request.method == 'POST':
        cart_json   = request.POST.get('cart_json', '[]')
        section     = request.POST.get('section', 'marche')
        montant_str = request.POST.get('montant', '0')

        # Second POST = confirmation finale (has 'methode')
        if 'methode' in request.POST:
            try:
                montant = Decimal(montant_str)
            except Exception:
                montant = Decimal('0')

            frais_livraison = Decimal('1000') if request.POST.get('mode_livraison') == 'livraison' else Decimal('0')
            montant_total   = montant + frais_livraison

            gps_lat_str = request.POST.get('gps_lat', '').strip()
            gps_lng_str = request.POST.get('gps_lng', '').strip()
            try:
                gps_lat = Decimal(gps_lat_str) if gps_lat_str else None
                gps_lng = Decimal(gps_lng_str) if gps_lng_str else None
            except Exception:
                gps_lat = gps_lng = None

            mode_liv  = request.POST.get('mode_livraison', 'livraison')
            methode   = request.POST.get('methode', 'especes')
            tel_mm    = request.POST.get('telephone_paiement', '').strip()
            MOBILE_MONEY = {'airtel_money', 'mtn_mobile', 'orange_money'}
            # Paiement validé immédiatement si mobile money + numéro fourni
            statut_init = 'valide' if (methode in MOBILE_MONEY and tel_mm) else 'en_attente'

            paiement = Paiement.objects.create(
                client             = request.user if request.user.is_authenticated else None,
                section            = section,
                montant            = montant,
                frais_livraison    = frais_livraison,
                frais_service      = Decimal('0'),
                montant_total      = montant_total,
                methode            = methode,
                telephone_paiement = tel_mm,
                mode_livraison     = mode_liv,
                quartier_livraison = request.POST.get('quartier', ''),
                adresse_livraison  = request.POST.get('adresse', ''),
                gps_lat            = gps_lat,
                gps_lng            = gps_lng,
                notes              = cart_json,
                statut             = statut_init,
            )
            # Créer la livraison et chercher un livreur si mode livraison
            if mode_liv == 'livraison':
                _assigner_livreur(paiement)
            return redirect('paiement_confirmation', pk=paiement.pk)

        # First POST = show checkout form
        try:
            cart_items = _json.loads(cart_json)
        except Exception:
            cart_items = []

        try:
            montant = Decimal(montant_str)
        except Exception:
            montant = sum(
                Decimal(str(i.get('prix', 0))) * int(i.get('quantite', 1))
                for i in cart_items
            )

        return render(request, 'paiement/checkout.html', {
            'cart_items':    cart_items,
            'cart_json':     cart_json,
            'section':       section,
            'section_label': SECTION_LABELS.get(section, section.title()),
            'montant':       montant,
            'frais_livraison': Decimal('1000'),
            'quartiers':     QUARTIERS_BZV,
            'methodes':      Paiement.METHODES,
        })

    # GET — redirect back
    return redirect('accueil')


def paiement_confirmation(request, pk):
    """Page de confirmation après création d'un paiement."""
    paiement = get_object_or_404(Paiement, pk=pk)
    if request.user.is_authenticated and paiement.client and paiement.client != request.user:
        return redirect('accueil')

    try:
        cart_items = _sanitize_cart_items(_json.loads(paiement.notes) if paiement.notes else [])
    except Exception:
        cart_items = []

    try:
        livraison = paiement.livraison
    except Exception:
        livraison = None

    return render(request, 'paiement/confirmation.html', {
        'paiement':   paiement,
        'cart_items': cart_items,
        'livraison':  livraison,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# LIVRAISON — logique d'attribution + workflow complet
# ═══════════════════════════════════════════════════════════════════════════════

def _assigner_livreur(paiement):
    """Génère l'OTP, cherche le livreur le plus proche, crée la Livraison."""
    import random
    from django.utils import timezone as tz
    otp = str(random.randint(100000, 999999))

    livreur = None
    if paiement.gps_lat and paiement.gps_lng:
        try:
            from django.contrib.gis.geos import Point
            from django.contrib.gis.db.models.functions import Distance
            pt = Point(float(paiement.gps_lng), float(paiement.gps_lat), srid=4326)
            livreur = (
                User.objects
                .filter(role='livreur', statut=True, last_location__isnull=False)
                .exclude(missions_livraison__statut__in=['accepte', 'en_recuperation', 'en_route'])
                .annotate(dist=Distance('last_location', pt))
                .order_by('dist')
                .first()
            )
        except Exception:
            pass
    # Pas de GPS : livraison créée en attente_livreur sans assignation automatique

    statut_init = 'assigne' if livreur else 'attente_livreur'
    livraison = Livraison.objects.create(
        paiement=paiement,
        livreur=livreur,
        livreur_nom_cache=livreur.get_full_name() if livreur else '',
        statut=statut_init,
        otp_code=otp,
        assigned_at=tz.now() if livreur else None,
    )

    try:
        from resto.services.fcm_service import send_push_notification
        if livreur and livreur.fcm_token:
            send_push_notification(
                fcm_token=livreur.fcm_token,
                title="🛵 Nouvelle mission !",
                body=f"Commande #{paiement.pk} — {paiement.quartier_livraison or 'adresse fournie'}",
                data={"livraison_id": str(livraison.pk), "type": "new_livraison"},
            )
        if paiement.client and paiement.client.fcm_token:
            # Étape 1 : commande reçue
            if livreur:
                # Étape 1+2 combinées : un livreur est déjà assigné automatiquement
                send_push_notification(
                    fcm_token=paiement.client.fcm_token,
                    title="✅ Commande reçue — Livreur trouvé !",
                    body=f"{livreur.get_full_name()} prendra en charge votre livraison.",
                    data={"paiement_id": str(paiement.pk), "type": "livreur_assigned"},
                )
            else:
                # Étape 1 : en attente d'un livreur
                send_push_notification(
                    fcm_token=paiement.client.fcm_token,
                    title="✅ Commande reçue !",
                    body="Nous recherchons un livreur disponible. Vous serez notifié(e) dès qu'un livreur est assigné.",
                    data={"paiement_id": str(paiement.pk), "type": "commande_recue"},
                )
    except Exception:
        pass
    return livraison


def suivi_livraison(request, pk):
    """Page de suivi de livraison pour le client."""
    paiement = get_object_or_404(Paiement, pk=pk)
    if request.user.is_authenticated and paiement.client and paiement.client != request.user:
        return redirect('accueil')
    try:
        livraison = paiement.livraison
    except Livraison.DoesNotExist:
        livraison = None

    steps = [
        ('assigne',         'Livreur assigné',           'person_pin'),
        ('accepte',         'Livreur en route',          'directions_bike'),
        ('en_recuperation', 'Récupération du colis',     'inventory_2'),
        ('en_route',        'En route vers vous',        'local_shipping'),
        ('livree',          'Commande livrée',           'check_circle'),
    ]
    order_map = {s: i for i, (s, _, __) in enumerate(steps)}
    current_idx = order_map.get(livraison.statut if livraison else '', -1)
    done_steps = {s for s, _, __ in steps[:current_idx]}

    return render(request, 'paiement/suivi_livraison.html', {
        'paiement': paiement, 'livraison': livraison,
        'steps': steps, 'done_steps': done_steps,
    })


@api_view(["GET"])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([AllowAny])
def suivi_position_api(request, pk):
    """JSON : position GPS actuelle du livreur + infos profil.
    Accepte JWT (mobile) et session (web). OTP visible uniquement au propriétaire authentifié.
    """
    paiement = get_object_or_404(Paiement, pk=pk)
    if request.user.is_authenticated and paiement.client and paiement.client != request.user:
        return Response({'error': 'forbidden'}, status=403)
    try:
        livraison = paiement.livraison
    except Livraison.DoesNotExist:
        return Response({'statut': 'no_livraison'})

    is_owner = request.user.is_authenticated and paiement.client and paiement.client == request.user
    show_otp = is_owner and livraison.statut == 'en_route' and not livraison.otp_valide

    data = {
        'statut':      livraison.statut,
        'otp_code':    livraison.otp_code if show_otp else None,
        'livreur':     None,
        'destination': {
            'lat': float(paiement.gps_lat) if paiement.gps_lat else None,
            'lng': float(paiement.gps_lng) if paiement.gps_lng else None,
        },
    }
    if livraison.livreur:
        lv = livraison.livreur
        try:
            _photo     = lv.livreur_profile.photo_url or ''
            _matricule = lv.livreur_profile.matricule_moto or ''
        except Exception:
            _photo     = ''
            _matricule = lv.matricule or ''
        if not _photo and lv.avatar:
            _photo = request.build_absolute_uri(lv.avatar.url)
        elif _photo and not _photo.startswith('http'):
            _photo = request.build_absolute_uri(_photo)
        data['livreur'] = {
            'nom':       lv.last_name,
            'prenom':    lv.first_name,
            'telephone': lv.telephone or '',
            'matricule': _matricule,
            'avatar':    _photo,
            'lat':       float(lv.last_lat) if lv.last_lat else None,
            'lng':       float(lv.last_lng) if lv.last_lng else None,
        }
    elif livraison.livreur_nom_cache:
        data['livreur_nom_cache'] = livraison.livreur_nom_cache
    return Response(data)


@login_required(login_url='/connexion/livreur/')
def livreur_update_position(request):
    """Le livreur envoie sa position GPS (POST JSON ou form)."""
    if request.user.role != 'livreur' or request.method != 'POST':
        return JsonResponse({'error': 'invalid'}, status=400)
    try:
        body = _json.loads(request.body)
        lat  = float(body.get('lat', 0))
        lng  = float(body.get('lng', 0))
    except Exception:
        lat = float(request.POST.get('lat', 0))
        lng = float(request.POST.get('lng', 0))
    if not lat or not lng:
        return JsonResponse({'error': 'missing coords'}, status=400)

    from django.contrib.gis.geos import Point
    from django.utils import timezone as tz
    request.user.last_lat = lat
    request.user.last_lng = lng
    request.user.last_location = Point(lng, lat, srid=4326)
    request.user.location_updated_at = tz.now()
    request.user.save(update_fields=['last_lat', 'last_lng', 'last_location', 'location_updated_at'])
    return JsonResponse({'ok': True})


@login_required(login_url='/connexion/livreur/')
def livreur_mes_missions(request):
    """Dashboard livraisons pour le livreur (remplace la vue livreur_dashboard)."""
    if request.user.role != 'livreur':
        return redirect('livreur_connexion')

    missions_dispo = (
        Livraison.objects
        .filter(statut='attente_livreur')
        .select_related('paiement__client')
        .order_by('-created_at')
    )
    mes_missions = (
        Livraison.objects
        .filter(livreur=request.user)
        .select_related('paiement__client')
        .order_by('-created_at')
    )
    total   = mes_missions.count()
    livrees = mes_missions.filter(statut='livree').count()
    en_cours = mes_missions.filter(statut__in=['accepte', 'en_recuperation', 'en_route']).count()

    return render(request, 'livreur/missions.html', {
        'missions_dispo': missions_dispo,
        'mes_missions':   mes_missions,
        'total': total, 'livrees': livrees, 'en_cours': en_cours,
        'nb_dispo': missions_dispo.count(),
    })


@login_required(login_url='/connexion/livreur/')
def livreur_accepter_mission(request, pk):
    """Le livreur accepte une mission disponible ou assignée."""
    if request.user.role != 'livreur':
        return redirect('livreur_connexion')
    from django.utils import timezone as tz
    from django.db import transaction
    with transaction.atomic():
        liv = get_object_or_404(
            Livraison.objects.select_for_update(),
            pk=pk, statut__in=['attente_livreur', 'assigne'],
        )
        if liv.statut == 'attente_livreur':
            liv.livreur = request.user
        elif liv.livreur and liv.livreur != request.user:
            messages.error(request, "Cette mission est déjà assignée à un autre livreur.")
            return redirect('livreur_mes_missions')
        liv.livreur_nom_cache = request.user.get_full_name()
        liv.statut = 'accepte'
        liv.accepted_at = tz.now()
        liv.save(update_fields=['livreur', 'livreur_nom_cache', 'statut', 'accepted_at'])

    if liv.paiement.client and liv.paiement.client.fcm_token:
        try:
            from resto.services.fcm_service import send_push_notification
            nom = request.user.get_full_name() or request.user.username
            send_push_notification(
                fcm_token=liv.paiement.client.fcm_token,
                title="🛵 Livreur en route vers le vendeur !",
                body=f"{nom} est en route pour récupérer votre commande.",
                data={"livraison_id": str(liv.pk), "paiement_id": str(liv.paiement_id), "type": "livreur_assigned"},
            )
        except Exception:
            pass

    messages.success(request, "Mission acceptée ! Rendez-vous chez le vendeur.")
    return redirect('livreur_mission_detail', pk=pk)


@login_required(login_url='/connexion/livreur/')
def livreur_mission_detail(request, pk):
    """Détail d'une mission + saisie OTP."""
    if request.user.role != 'livreur':
        return redirect('livreur_connexion')
    liv = get_object_or_404(Livraison, pk=pk, livreur=request.user)
    cart_items = _sanitize_cart_items(_json.loads(liv.paiement.notes) if liv.paiement.notes else [])
    return render(request, 'livreur/mission_detail.html', {'liv': liv, 'cart_items': cart_items})


@login_required(login_url='/connexion/livreur/')
def livreur_maj_statut(request, pk):
    """Avancement du statut : accepte → en_recuperation → en_route."""
    if request.user.role != 'livreur' or request.method != 'POST':
        return redirect('livreur_mes_missions')
    from django.utils import timezone as tz
    liv = get_object_or_404(Livraison, pk=pk, livreur=request.user)
    transitions = {
        'accepte':         ('en_recuperation', None,         "En route vers le vendeur 🚴"),
        'en_recuperation': ('en_route',         'picked_at',  "Colis récupéré — en route vers le client 🛵"),
    }
    if liv.statut in transitions:
        nouveau_statut, champ_ts, msg = transitions[liv.statut]
        liv.statut = nouveau_statut
        if champ_ts:
            setattr(liv, champ_ts, tz.now())
        liv.save()
        messages.success(request, msg)
        if liv.paiement.client and liv.paiement.client.fcm_token:
            try:
                from resto.services.fcm_service import send_push_notification
                if nouveau_statut == 'en_route':
                    send_push_notification(
                        fcm_token=liv.paiement.client.fcm_token,
                        title="🛵 Votre livreur est en route !",
                        body=f"Code de confirmation : {liv.otp_code} — À remettre au livreur lors de la réception.",
                        data={"livraison_id": str(liv.pk), "paiement_id": str(liv.paiement_id), "otp": liv.otp_code, "type": "livreur_en_route"},
                    )
                else:
                    send_push_notification(
                        fcm_token=liv.paiement.client.fcm_token,
                        title="📦 Récupération du colis en cours",
                        body="Le livreur est chez le vendeur et récupère votre commande.",
                        data={"livraison_id": str(liv.pk), "paiement_id": str(liv.paiement_id), "type": "livraison_update"},
                    )
            except Exception:
                pass
    return redirect('livreur_mission_detail', pk=pk)


@login_required(login_url='/connexion/livreur/')
def livreur_valider_otp(request, pk):
    """Valide le code OTP pour finaliser la livraison."""
    if request.user.role != 'livreur' or request.method != 'POST':
        return redirect('livreur_mes_missions')
    from django.utils import timezone as tz
    liv = get_object_or_404(Livraison, pk=pk, livreur=request.user, statut='en_route')
    otp_saisi = request.POST.get('otp', '').strip()
    if otp_saisi == liv.otp_code:
        liv.statut = 'livree'
        liv.otp_valide = True
        liv.delivered_at = tz.now()
        liv.save()
        liv.paiement.statut = 'valide'
        liv.paiement.save(update_fields=['statut'])
        messages.success(request, "Livraison validée avec succès ! ✅")
        if liv.paiement.client and liv.paiement.client.fcm_token:
            try:
                from resto.services.fcm_service import send_push_notification
                send_push_notification(
                    fcm_token=liv.paiement.client.fcm_token,
                    title="✅ Commande livrée !",
                    body="Votre commande a été livrée. Merci !",
                    data={"livraison_id": str(liv.pk), "paiement_id": str(liv.paiement_id), "type": "livraison_done"},
                )
            except Exception:
                pass
    else:
        messages.error(request, "Code OTP incorrect. Vérifiez avec le client.")
    return redirect('livreur_mission_detail', pk=pk)


@login_required
def vendeur_marquer_commande(request, pk):
    """Vendeur ou admin marque la commande comme en préparation ou prête."""
    if request.method != 'POST':
        return redirect('vendeur_commandes')
    paiement = get_object_or_404(Paiement, pk=pk)
    nouveau_statut = request.POST.get('statut_preparation')
    if nouveau_statut in ('en_preparation', 'pret'):
        paiement.statut_preparation = nouveau_statut
        paiement.save(update_fields=['statut_preparation'])
        if nouveau_statut == 'pret' and paiement.mode_livraison == 'livraison':
            messages.success(request, f"Commande #{pk} prête. Choisissez un livreur.")
            return redirect('assigner_livreur_page', pk=pk)
        if nouveau_statut == 'pret' and paiement.mode_livraison == 'retrait':
            messages.success(request, f"Commande #{pk} prête — en attente du retrait client.")
        else:
            label = "En préparation" if nouveau_statut == 'en_preparation' else "Prête à livrer"
            messages.success(request, f"Commande #{pk} : {label}")
    elif nouveau_statut == 'confirmer_retrait_client':
        # Vendeur confirme que le client est venu chercher la commande
        if paiement.mode_livraison == 'retrait':
            paiement.statut = 'valide'
            from django.utils import timezone as _tz
            paiement.valide_le = _tz.now()
            paiement.save(update_fields=['statut', 'valide_le'])
            if paiement.client and paiement.client.fcm_token:
                try:
                    from resto.services.fcm_service import send_push_notification
                    send_push_notification(
                        fcm_token=paiement.client.fcm_token,
                        title="✅ Retrait confirmé !",
                        body="Votre commande a été récupérée en boutique. Merci !",
                        data={"paiement_id": str(paiement.pk), "type": "retrait_confirme"},
                    )
                except Exception:
                    pass
            messages.success(request, f"Commande #{pk} : Retrait confirmé ✅")
        else:
            messages.error(request, "Cette commande n'est pas en mode retrait.")
    # Retour intelligent : admin ou vendeur
    if request.user.role == 'admin':
        return redirect('admin_panel_commandes')
    return redirect('vendeur_paiement_detail', pk=pk)


@login_required(login_url='/connexion/livreur/')
def livreur_mission_map_api(request, pk):
    """JSON : positions client, vendeur, livreur pour la carte de mission."""
    if request.user.role != 'livreur':
        return JsonResponse({'error': 'forbidden'}, status=403)

    liv = get_object_or_404(Livraison, pk=pk, livreur=request.user)
    paiement = liv.paiement

    # ── Position client ──────────────────────────────────────────────────────
    client_data = None
    if paiement.gps_lat and paiement.gps_lng:
        nom = paiement.client.get_full_name() if paiement.client else 'Client'
        client_data = {
            'lat': float(paiement.gps_lat),
            'lng': float(paiement.gps_lng),
            'nom': nom,
            'quartier': paiement.quartier_livraison or '',
            'adresse':  paiement.adresse_livraison or '',
        }

    # ── Position vendeur ─────────────────────────────────────────────────────
    vendeur_data = None
    try:
        from boutique.models import Boutique as _BoutiqueModel
        # Chercher via le nom de boutique dans le panier
        boutique = None
        if paiement.notes:
            items = _json.loads(paiement.notes)
            if items:
                nom_boutique = items[0].get('vendeur', '')
                if nom_boutique:
                    boutique = _BoutiqueModel.objects.filter(nom=nom_boutique).first()

        if boutique and boutique.position:
            vendeur_data = {
                'lat': float(boutique.position.y),
                'lng': float(boutique.position.x),
                'nom': boutique.nom,
                'adresse': boutique.adresse_exacte or '',
            }
        else:
            # Fallback : GPS du propriétaire de boutique en section correspondante
            b = _BoutiqueModel.objects.filter(
                type_commerce__icontains=paiement.section,
                user__last_lat__isnull=False,
            ).select_related('user').first()
            if b and b.user.last_lat:
                vendeur_data = {
                    'lat': float(b.user.last_lat),
                    'lng': float(b.user.last_lng),
                    'nom': b.nom,
                    'adresse': b.adresse_exacte or '',
                }
    except Exception:
        pass

    # ── Position livreur (depuis DB, mis à jour par le GPS du livreur) ───────
    livreur_data = None
    if liv.livreur and liv.livreur.last_lat:
        livreur_data = {
            'lat': float(liv.livreur.last_lat),
            'lng': float(liv.livreur.last_lng),
            'nom': liv.livreur.get_full_name(),
            'updated_at': liv.livreur.location_updated_at.isoformat() if liv.livreur.location_updated_at else None,
        }

    return JsonResponse({
        'statut': liv.statut,
        'client':  client_data,
        'vendeur': vendeur_data,
        'livreur': livreur_data,
    })


@login_required
def assigner_livreur_page(request, pk):
    """Page carte : sélectionner et notifier les livreurs proches."""
    paiement = get_object_or_404(Paiement, pk=pk)
    if request.user.role not in ('admin', 'vendeur'):
        return redirect('accueil')

    if request.method == 'POST':
        import random
        from django.utils import timezone as tz

        livreur_ids = request.POST.getlist('livreur_ids')
        if not livreur_ids:
            messages.error(request, "Sélectionnez au moins un livreur.")
            return redirect('assigner_livreur_page', pk=pk)

        otp = str(random.randint(100000, 999999))

        # Créer ou récupérer la Livraison
        try:
            livraison = paiement.livraison
            if livraison.statut not in ('attente_livreur',):
                messages.info(request, "Un livreur est déjà assigné à cette commande.")
                return redirect('vendeur_paiement_detail', pk=pk)
        except Livraison.DoesNotExist:
            livraison = Livraison.objects.create(
                paiement=paiement,
                livreur=None,
                statut='attente_livreur',
                otp_code=otp,
            )

        # Envoyer notification FCM aux livreurs sélectionnés
        livreurs_notifies = User.objects.filter(pk__in=livreur_ids, role='livreur')
        for lv in livreurs_notifies:
            if lv.fcm_token:
                try:
                    from resto.services.fcm_service import send_push_notification
                    send_push_notification(
                        fcm_token=lv.fcm_token,
                        title="🛵 Nouvelle mission disponible !",
                        body=f"Commande #{paiement.pk} — {paiement.quartier_livraison or 'Brazzaville'} — {int(paiement.montant_total)} FCFA",
                        data={"livraison_id": str(livraison.pk), "type": "new_livraison"},
                    )
                except Exception:
                    pass

        nb = livreurs_notifies.count()
        messages.success(request, f"{nb} livreur(s) notifié(s). Le premier à accepter récupérera la mission.")
        if request.user.role == 'admin':
            return redirect('admin_panel_commandes')
        return redirect('vendeur_paiement_detail', pk=pk)

    return render(request, 'paiement/assigner_livreur.html', {'paiement': paiement})


@login_required
def api_livreurs_proches(request, pk):
    """JSON : tous les livreurs actifs avec distance et statut GPS."""
    import math
    from django.utils import timezone as _tz
    paiement = get_object_or_404(Paiement, pk=pk)
    if request.user.role not in ('admin', 'vendeur'):
        return JsonResponse({'error': 'forbidden'}, status=403)

    # Tous les livreurs dont le compte est actif, sans aucune exclusion
    qs = (
        User.objects
        .filter(role='livreur', statut=True)
        .select_related('livreur_profile')
        .prefetch_related('missions_livraison')
        .order_by('last_name', 'first_name')
    )

    now = _tz.now()
    livreurs = []
    for lv in qs:
        dist_km = None
        if paiement.gps_lat and paiement.gps_lng and lv.last_lat and lv.last_lng:
            lat1, lng1 = float(paiement.gps_lat), float(paiement.gps_lng)
            lat2, lng2 = float(lv.last_lat), float(lv.last_lng)
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlng/2)**2
            dist_km = round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)), 1)

        # En ligne = GPS mis à jour dans les 5 dernières minutes (heartbeat 60 s)
        gps_ok = bool(lv.last_lat and lv.last_lng)
        en_ligne = False
        gps_age_min = None
        if lv.location_updated_at and gps_ok:
            delta = now - lv.location_updated_at
            gps_age_min = int(delta.total_seconds() / 60)
            en_ligne = gps_age_min <= 5

        # Mission en cours ?
        en_mission = lv.missions_livraison.filter(
            statut__in=['accepte', 'en_recuperation', 'en_route']
        ).exists()

        try:
            _avatar = lv.livreur_profile.photo_url or lv.avatar_url
        except Exception:
            _avatar = lv.avatar_url

        livreurs.append({
            'id':          lv.pk,
            'nom':         lv.last_name,
            'prenom':      lv.first_name,
            'telephone':   lv.telephone or '',
            'matricule':   lv.matricule or '',
            'avatar':      _avatar,
            'lat':         float(lv.last_lat) if gps_ok else None,
            'lng':         float(lv.last_lng) if gps_ok else None,
            'dist_km':     dist_km,
            'en_ligne':    en_ligne,
            'en_mission':  en_mission,
            'gps_ok':      gps_ok,
            'gps_age_min': gps_age_min,
        })

    # Tri : disponibles en ligne > disponibles hors ligne > en mission
    def sort_key(x):
        if x['en_ligne'] and not x['en_mission']:
            return (0, x['dist_km'] is None, x['dist_km'] or 999)
        if not x['en_mission']:
            return (1, x['dist_km'] is None, x['dist_km'] or 999)
        return (2, x['dist_km'] is None, x['dist_km'] or 999)

    livreurs.sort(key=sort_key)

    return JsonResponse({
        'client': {
            'lat': float(paiement.gps_lat) if paiement.gps_lat else None,
            'lng': float(paiement.gps_lng) if paiement.gps_lng else None,
            'adresse': paiement.adresse_livraison or paiement.quartier_livraison or '',
        },
        'total':      len(livreurs),
        'en_ligne':   sum(1 for l in livreurs if l['en_ligne'] and not l['en_mission']),
        'disponibles': sum(1 for l in livreurs if not l['en_mission']),
        'livreurs':   livreurs,
    })


@login_required(login_url='/connexion/livreur/')
def api_livreur_missions_poll(request):
    """JSON : missions disponibles + stats (polling AJAX pour la page missions)."""
    if request.user.role != 'livreur':
        return JsonResponse({'error': 'forbidden'}, status=403)

    from django.utils import timezone as _tz
    now = _tz.now()

    def _age(dt):
        secs = int((now - dt).total_seconds())
        if secs < 60:
            return "à l'instant"
        elif secs < 3600:
            return f"il y a {secs // 60} min"
        elif secs < 86400:
            return f"il y a {secs // 3600}h"
        return dt.strftime('%d/%m %H:%M')

    missions = (
        Livraison.objects
        .filter(statut='attente_livreur')
        .select_related('paiement__client')
        .order_by('-created_at')
    )

    data = [
        {
            'pk':            liv.pk,
            'paiement_pk':   liv.paiement.pk,
            'section':       liv.paiement.get_section_display(),
            'montant_total': float(liv.paiement.montant_total),
            'quartier':      liv.paiement.quartier_livraison or 'Quartier non précisé',
            'adresse':       (liv.paiement.adresse_livraison or '')[:60],
            'age':           _age(liv.created_at),
            'accept_url':    f'/livreur/missions/{liv.pk}/accepter/',
        }
        for liv in missions
    ]

    return JsonResponse({'missions': data, 'nb_dispo': len(data)})


@login_required
def api_vendeur_commandes_poll(request):
    """JSON : nouvelles commandes complètes depuis un timestamp (polling AJAX)."""
    vp = getattr(request.user, 'vendeur_profile', None)
    if not vp and request.user.role not in ('vendeur', 'admin'):
        return JsonResponse({'error': 'forbidden'}, status=403)

    from django.utils import timezone as _tz
    import datetime

    since_str = request.GET.get('since', '')
    try:
        since = datetime.datetime.fromisoformat(since_str)
        if since.tzinfo is None:
            since = since.replace(tzinfo=datetime.timezone.utc)
    except (ValueError, TypeError):
        since = _tz.now()

    # Fixer le plafond AVANT la requête pour ne rien rater entre la query et la réponse
    now = _tz.now()

    boutiques = _Boutique.objects.filter(user=request.user)
    sections = _boutiques_to_sections(boutiques)
    if vp and vp.section and vp.section not in sections:
        sections.append(vp.section)

    nouvelles_qs = (
        Paiement.objects
        .filter(section__in=sections, cree_le__gt=since, cree_le__lte=now)
        .select_related('client')
        .order_by('-cree_le')
        if sections else Paiement.objects.none()
    )

    def _serialize(p):
        return {
            'id':                  p.pk,
            'client_nom':          p.client.get_full_name() if p.client else '—',
            'client_tel':          getattr(p.client, 'telephone', '') if p.client else '',
            'section':             p.get_section_display(),
            'montant':             float(p.montant_total),
            'date':                p.cree_le.strftime('%d/%m/%Y %H:%M'),
            'mode_livraison':      p.get_mode_livraison_display(),
            'mode_livraison_code': p.mode_livraison,
            'statut':              p.get_statut_display(),
            'statut_code':         p.statut,
            'url':                 f'/vendeur/paiements/{p.pk}/',
        }

    data = [_serialize(p) for p in nouvelles_qs]
    return JsonResponse({'nouvelles': data, 'nb': len(data), 'server_time': now.isoformat()})


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT — Profil, commandes
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def client_profil(request):
    user = request.user
    if request.method == 'POST':
        from .forms import UserUpdateForm
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour ✅")
            return redirect('client_profil')
    else:
        from .forms import UserUpdateForm
        form = UserUpdateForm(instance=user)

    # Stats
    paiements = Paiement.objects.filter(client=user)
    total_commandes = paiements.count()
    total_depenses  = sum(p.montant_total for p in paiements if p.statut == 'valide') or 0
    en_cours        = paiements.filter(statut='en_attente').count()
    recentes        = paiements.order_by('-cree_le')[:5]

    return render(request, 'client/profil.html', {
        'form':            form,
        'total_commandes': total_commandes,
        'total_depenses':  total_depenses,
        'en_cours':        en_cours,
        'recentes':        recentes,
    })


@login_required
def client_commandes(request):
    user       = request.user
    paiements  = Paiement.objects.filter(client=user).select_related('livraison')

    statut_filter  = request.GET.get('statut', '')
    section_filter = request.GET.get('section', '')
    if statut_filter:
        paiements = paiements.filter(statut=statut_filter)
    if section_filter:
        paiements = paiements.filter(section=section_filter)

    paiements = paiements.order_by('-cree_le')

    return render(request, 'client/commandes.html', {
        'paiements':      paiements,
        'statut_filter':  statut_filter,
        'section_filter': section_filter,
        'statuts':        Paiement.STATUTS,
        'sections':       Paiement.SECTIONS,
    })


@login_required
def client_commande_detail(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk, client=request.user)
    try:
        cart_items = _sanitize_cart_items(_json.loads(paiement.notes) if paiement.notes else [])
    except Exception:
        cart_items = []
    return render(request, 'client/commande_detail.html', {
        'paiement':   paiement,
        'cart_items': cart_items,
    })


# ════════════════════════════════════════════════════════════════════════
# ══  ADMIN PANEL  ═══════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════

def _is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

def _admin_required(view_func):
    decorated = login_required(user_passes_test(_is_admin, login_url='/connexion/')(view_func))
    return decorated


@_admin_required
def admin_panel_dashboard(request):
    from django.db.models import Sum, Count, Q as DQ
    from .models import VendeurProfile, Paiement
    from shopping.models import Shop

    stats = {
        'clients':      User.objects.filter(role='client').count(),
        'vendeurs':     User.objects.filter(role='vendeur').count(),
        'livreurs':     User.objects.filter(role='livreur').count(),
        'total_users':  User.objects.count(),
        'commandes':    Paiement.objects.count(),
        'en_attente':   Paiement.objects.filter(statut='en_attente').count(),
        'revenue':      Paiement.objects.filter(statut='valide').aggregate(s=Sum('montant_total'))['s'] or 0,
        'boutiques':    Shop.objects.filter(active=True).count(),
        'vendeur_actifs': VendeurProfile.objects.filter(actif=True).count(),
    }

    section_stats = list(
        Paiement.objects.values('section')
        .annotate(nb=Count('id'), rev=Sum('montant_total'))
        .order_by('-nb')
    )

    recent_commandes = (
        Paiement.objects.select_related('client')
        .order_by('-cree_le')[:8]
    )
    recent_users = User.objects.order_by('-date_inscription')[:8]

    return render(request, 'admin_panel/dashboard.html', {
        'stats': stats,
        'section_stats': section_stats,
        'recent_commandes': recent_commandes,
        'recent_users': recent_users,
    })


@_admin_required
def admin_panel_utilisateurs(request):
    from django.db.models import Q as DQ
    from django.core.paginator import Paginator

    role_filter = request.GET.get('role', '')
    q = request.GET.get('q', '').strip()

    users = User.objects.all().order_by('-date_inscription')
    if role_filter:
        users = users.filter(role=role_filter)
    if q:
        users = users.filter(
            DQ(first_name__icontains=q) | DQ(username__icontains=q) | DQ(telephone__icontains=q)
        )

    if request.method == 'POST':
        uid = request.POST.get('user_id')
        action = request.POST.get('action')
        target = get_object_or_404(User, pk=uid)
        if action == 'toggle_statut':
            target.statut = not target.statut
            target.save(update_fields=['statut'])
        elif action == 'change_role':
            new_role = request.POST.get('new_role', '')
            if new_role in ['client', 'admin', 'employe', 'livreur', 'vendeur']:
                target.role = new_role
                target.save(update_fields=['role'])
        return redirect(request.get_full_path())

    paginator = Paginator(users, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_panel/utilisateurs.html', {
        'page_obj': page_obj,
        'role_filter': role_filter,
        'q': q,
        'roles': [('', 'Tous'), ('client', 'Clients'), ('vendeur', 'Vendeurs'),
                  ('livreur', 'Livreurs'), ('admin', 'Admins'), ('employe', 'Employés')],
    })


@_admin_required
def admin_panel_vendeurs(request):
    from django.db.models import Q as DQ
    from django.core.paginator import Paginator
    from .models import VendeurProfile

    section_filter = request.GET.get('section', '')
    q = request.GET.get('q', '').strip()

    # Tous les users role=vendeur, VendeurProfile optionnel
    vendeurs = (
        User.objects
        .filter(role='vendeur')
        .select_related('vendeur_profile')
        .prefetch_related('mes_boutiques')
        .order_by('-date_inscription')
    )
    if section_filter:
        vendeurs = vendeurs.filter(vendeur_profile__section=section_filter)
    if q:
        vendeurs = vendeurs.filter(
            DQ(first_name__icontains=q) |
            DQ(last_name__icontains=q)  |
            DQ(telephone__icontains=q)  |
            DQ(vendeur_profile__nom_commercial__icontains=q)
        )

    if request.method == 'POST':
        action  = request.POST.get('action')
        user_id = request.POST.get('user_id')
        target  = get_object_or_404(User, pk=user_id, role='vendeur')
        if action == 'toggle_actif':
            target.statut = not target.statut
            target.save(update_fields=['statut'])
            try:
                target.vendeur_profile.actif = target.statut
                target.vendeur_profile.save(update_fields=['actif'])
            except VendeurProfile.DoesNotExist:
                pass
        return redirect(request.get_full_path())

    paginator = Paginator(vendeurs, 25)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_panel/vendeurs.html', {
        'page_obj':       page_obj,
        'section_filter': section_filter,
        'q':              q,
        'sections':       VendeurProfile.SECTIONS,
    })


@_admin_required
def admin_panel_commandes(request):
    from django.db.models import Q as DQ
    from django.core.paginator import Paginator
    from .models import Paiement

    statut_filter = request.GET.get('statut', '')
    section_filter = request.GET.get('section', '')
    q = request.GET.get('q', '').strip()

    commandes = Paiement.objects.select_related('client').order_by('-cree_le')
    if statut_filter:
        commandes = commandes.filter(statut=statut_filter)
    if section_filter:
        commandes = commandes.filter(section=section_filter)
    if q:
        commandes = commandes.filter(
            DQ(client__first_name__icontains=q) |
            DQ(client__telephone__icontains=q) |
            DQ(id__icontains=q)
        )

    if request.method == 'POST':
        paiement_id = request.POST.get('paiement_id')
        new_statut = request.POST.get('statut')
        paiement = get_object_or_404(Paiement, pk=paiement_id)
        if new_statut in dict(Paiement.STATUTS):
            paiement.statut = new_statut
            if new_statut == 'valide' and not paiement.valide_le:
                from django.utils import timezone
                paiement.valide_le = timezone.now()
            paiement.save(update_fields=['statut', 'valide_le'])
        return redirect(request.get_full_path())

    paginator = Paginator(commandes, 30)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_panel/commandes.html', {
        'page_obj': page_obj,
        'statut_filter': statut_filter,
        'section_filter': section_filter,
        'q': q,
        'statuts': Paiement.STATUTS,
        'sections': Paiement.SECTIONS,
    })


@_admin_required
def admin_panel_boutiques(request):
    from django.db.models import Q as DQ
    from django.core.paginator import Paginator
    from shopping.models import Shop

    q = request.GET.get('q', '').strip()
    shops = Shop.objects.select_related('vendor', 'vendor__user').order_by('-created_at')
    if q:
        shops = shops.filter(
            DQ(name__icontains=q) |
            DQ(vendor__business_name__icontains=q)
        )

    if request.method == 'POST':
        action = request.POST.get('action')
        shop_id = request.POST.get('shop_id')
        shop = get_object_or_404(Shop, pk=shop_id)
        if action == 'toggle_active':
            shop.active = not shop.active
            shop.save(update_fields=['active'])
        return redirect(request.get_full_path())

    paginator = Paginator(shops, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_panel/boutiques.html', {
        'page_obj': page_obj,
        'q': q,
    })


@_admin_required
def admin_panel_livreurs(request):
    from django.db.models import Q as DQ
    from django.core.paginator import Paginator

    q = request.GET.get('q', '').strip()
    livreurs = User.objects.filter(role='livreur').order_by('-date_inscription')
    if q:
        livreurs = livreurs.filter(
            DQ(first_name__icontains=q) | DQ(telephone__icontains=q)
        )

    if request.method == 'POST':
        action = request.POST.get('action')
        livreur_id = request.POST.get('livreur_id')
        livreur = get_object_or_404(User, pk=livreur_id)
        if action == 'toggle_statut':
            livreur.statut = not livreur.statut
            livreur.save(update_fields=['statut'])
        return redirect(request.get_full_path())

    paginator = Paginator(livreurs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_panel/livreurs.html', {
        'page_obj': page_obj,
        'q': q,
    })


# ════════════════════════════════════════════════════════════════════════════
# ══  ADMIN — GESTION PRODUITS  ══════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════════

@_admin_required
def admin_produits_hub(request):
    from marche.models import Produit as MProduit
    from shopping.models import Product as SProduit, Shop
    from perruque.models import WigProduct
    from voiture.models import Car
    from immobilier.models import Immobilier
    from quicaillerie.models import ProduitQuincaillerie
    stats = {
        'marche':        MProduit.objects.count(),
        'shopping':      SProduit.objects.count(),
        'perruque':      WigProduct.objects.count(),
        'voiture':       Car.objects.count(),
        'immobilier':    Immobilier.objects.count(),
        'quicaillerie':  ProduitQuincaillerie.objects.count(),
    }
    return render(request, 'admin_panel/produits/hub.html', {'stats': stats})


# ── Marché ────────────────────────────────────────────────────────────────────

@_admin_required
def admin_produits_marche(request):
    from django import forms as dforms
    from marche.models import Produit, Categorie, Marche
    from boutique.models import Boutique
    from django.core.paginator import Paginator

    class ProduitMarcheAdminForm(dforms.ModelForm):
        class Meta:
            model = Produit
            fields = ['nom', 'vendeur', 'categorie', 'marche', 'prix', 'prix_promo',
                      'devise', 'unite', 'stock', 'description', 'image', 'disponibilite']
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            _s = 'w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-300'
            for f in self.fields.values():
                if not isinstance(f.widget, (dforms.CheckboxInput, dforms.FileInput)):
                    f.widget.attrs['class'] = _s
            self.fields['vendeur'].queryset = Boutique.objects.filter(actif=True).order_by('nom')
            self.fields['categorie'].queryset = Categorie.objects.order_by('nom')
            self.fields['marche'].queryset = Marche.objects.filter(actif=True).order_by('nom')
            self.fields['categorie'].required = False
            self.fields['marche'].required = False
            self.fields['prix_promo'].required = False
            self.fields['description'].required = False

    if request.method == 'POST':
        form = ProduitMarcheAdminForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit marché créé.")
            return redirect('admin_produits_marche')
    else:
        form = ProduitMarcheAdminForm()

    produits = Produit.objects.select_related('vendeur', 'categorie').order_by('-date_creation')
    paginator = Paginator(produits, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/produits/marche.html', {'form': form, 'page_obj': page_obj})


# ── Shopping ──────────────────────────────────────────────────────────────────

@_admin_required
def admin_produits_shopping(request):
    from django import forms as dforms
    from shopping.models import Product, Category
    from boutique.models import Boutique
    from django.core.paginator import Paginator
    from django.utils.text import slugify
    import uuid as _uuid

    class ProduitShoppingAdminForm(dforms.ModelForm):
        class Meta:
            model = Product
            fields = ['name', 'shop', 'category', 'price', 'prix_promo', 'stock', 'description', 'active']
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            _s = 'w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-pink-200'
            for f in self.fields.values():
                if not isinstance(f.widget, dforms.CheckboxInput):
                    f.widget.attrs['class'] = _s
            self.fields['shop'].queryset = Boutique.objects.filter(actif=True).order_by('nom')
            self.fields['category'].queryset = Category.objects.order_by('name')
            self.fields['category'].required = False
            self.fields['prix_promo'].required = False
        def save(self, commit=True):
            obj = super().save(commit=False)
            if not obj.slug:
                base = slugify(obj.name) or str(_uuid.uuid4())[:8]
                slug = base
                n = 1
                while Product.objects.filter(slug=slug).exists():
                    slug = f"{base}-{n}"; n += 1
                obj.slug = slug
            if commit:
                obj.save()
            return obj

    if request.method == 'POST':
        form = ProduitShoppingAdminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit shopping créé.")
            return redirect('admin_produits_shopping')
    else:
        form = ProduitShoppingAdminForm()

    produits = Product.objects.select_related('shop', 'category').order_by('-created_at')
    paginator = Paginator(produits, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/produits/shopping.html', {'form': form, 'page_obj': page_obj})


# ── Perruque ──────────────────────────────────────────────────────────────────

@_admin_required
def admin_produits_perruque(request):
    from django import forms as dforms
    from perruque.models import WigProduct, Category
    from boutique.models import Boutique
    from django.core.paginator import Paginator

    class WigAdminForm(dforms.ModelForm):
        class Meta:
            model = WigProduct
            fields = ['name', 'shop', 'category', 'price', 'promotional_price',
                      'color', 'length', 'texture', 'material', 'stock_quantity',
                      'description', 'status']
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            _s = 'w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-200'
            for f in self.fields.values():
                if not isinstance(f.widget, (dforms.CheckboxInput, dforms.Select)):
                    f.widget.attrs['class'] = _s
                elif isinstance(f.widget, dforms.Select):
                    f.widget.attrs['class'] = _s
            self.fields['shop'].queryset = Boutique.objects.filter(actif=True).order_by('nom')
            self.fields['category'].queryset = Category.objects.order_by('name')
            self.fields['category'].required = False
            self.fields['promotional_price'].required = False

    if request.method == 'POST':
        form = WigAdminForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit perruque créé.")
            return redirect('admin_produits_perruque')
    else:
        form = WigAdminForm()

    produits = WigProduct.objects.select_related('shop').order_by('-created_at')
    paginator = Paginator(produits, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/produits/perruque.html', {'form': form, 'page_obj': page_obj})


# ── Quincaillerie ─────────────────────────────────────────────────────────────

@_admin_required
def admin_produits_quicaillerie(request):
    from django import forms as dforms
    from quicaillerie.models import ProduitQuincaillerie, CategorieQuincaillerie
    from boutique.models import Boutique
    from django.core.paginator import Paginator

    class QuicAdminForm(dforms.ModelForm):
        class Meta:
            model = ProduitQuincaillerie
            fields = ['nom', 'boutique', 'categorie', 'prix', 'prix_promotionnel',
                      'marque', 'reference', 'unite', 'quantite_stock', 'description', 'statut']
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            _s = 'w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-200'
            for f in self.fields.values():
                if not isinstance(f.widget, dforms.Select):
                    f.widget.attrs['class'] = _s
                else:
                    f.widget.attrs['class'] = _s
            self.fields['boutique'].queryset = Boutique.objects.filter(actif=True).order_by('nom')
            self.fields['categorie'].queryset = CategorieQuincaillerie.objects.order_by('nom')
            self.fields['categorie'].required = False
            self.fields['prix_promotionnel'].required = False
            self.fields['marque'].required = False
            self.fields['reference'].required = False

    if request.method == 'POST':
        form = QuicAdminForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit quincaillerie créé.")
            return redirect('admin_produits_quicaillerie')
    else:
        form = QuicAdminForm()

    produits = ProduitQuincaillerie.objects.select_related('boutique').order_by('-date_creation')
    paginator = Paginator(produits, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/produits/quicaillerie.html', {'form': form, 'page_obj': page_obj})


# ── Voiture ───────────────────────────────────────────────────────────────────

@_admin_required
def admin_produits_voiture(request):
    from django import forms as dforms
    from voiture.models import Car, CarCategory
    from boutique.models import Boutique
    from django.core.paginator import Paginator

    class CarAdminForm(dforms.ModelForm):
        class Meta:
            model = Car
            fields = ['brand', 'model', 'year', 'shop', 'category', 'daily_price',
                      'promotional_price', 'seats', 'doors', 'transmission', 'fuel',
                      'air_conditioning', 'driver_included', 'city', 'description', 'status']
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            _s = 'w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200'
            for f in self.fields.values():
                if not isinstance(f.widget, (dforms.CheckboxInput, dforms.Select)):
                    f.widget.attrs['class'] = _s
                elif isinstance(f.widget, dforms.Select):
                    f.widget.attrs['class'] = _s
            self.fields['shop'].queryset = Boutique.objects.filter(actif=True).order_by('nom')
            self.fields['category'].queryset = CarCategory.objects.order_by('name')
            self.fields['category'].required = False
            self.fields['promotional_price'].required = False
            self.fields['city'].required = False

    if request.method == 'POST':
        form = CarAdminForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Véhicule créé.")
            return redirect('admin_produits_voiture')
    else:
        form = CarAdminForm()

    voitures = Car.objects.select_related('shop', 'category').order_by('-created_at')
    paginator = Paginator(voitures, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/produits/voiture.html', {'form': form, 'page_obj': page_obj})


# ── Immobilier ────────────────────────────────────────────────────────────────

@_admin_required
def admin_produits_immobilier(request):
    from django import forms as dforms
    from immobilier.models import Immobilier, ImmobilierCategory
    from boutique.models import Boutique
    from django.core.paginator import Paginator

    class ImmoAdminForm(dforms.ModelForm):
        class Meta:
            model = Immobilier
            fields = ['titre', 'vendeur', 'categorie', 'type_bien', 'type_offre',
                      'prix', 'prix_promotionnel', 'superficie', 'nombre_chambres',
                      'nombre_salles_bain', 'meuble', 'statut', 'description']
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            _s = 'w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-200'
            for f in self.fields.values():
                if not isinstance(f.widget, (dforms.CheckboxInput, dforms.Select)):
                    f.widget.attrs['class'] = _s
                elif isinstance(f.widget, dforms.Select):
                    f.widget.attrs['class'] = _s
            self.fields['vendeur'].queryset = Boutique.objects.filter(actif=True).order_by('nom')
            self.fields['categorie'].queryset = ImmobilierCategory.objects.order_by('nom')
            self.fields['categorie'].required = False
            self.fields['prix_promotionnel'].required = False

    if request.method == 'POST':
        form = ImmoAdminForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Bien immobilier créé.")
            return redirect('admin_produits_immobilier')
    else:
        form = ImmoAdminForm()

    biens = Immobilier.objects.select_related('vendeur').order_by('-date_creation')
    paginator = Paginator(biens, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/produits/immobilier.html', {'form': form, 'page_obj': page_obj})


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — Suivi des positions (temps réel)
# ══════════════════════════════════════════════════════════════════════════════

import json as _json_pos
from django.utils import timezone as _tz

def _admin_required_view(view_func):
    from functools import wraps
    @wraps(view_func)
    def _w(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('connexion_client')
        if not (request.user.is_superuser or request.user.role in ('admin', 'employe')):
            return redirect('accueil')
        return view_func(request, *args, **kwargs)
    return _w


@_admin_required_view
def admin_positions(request):
    """Page de suivi GPS de tous les utilisateurs."""
    users_with_pos = (
        User.objects
        .filter(last_lat__isnull=False, last_lng__isnull=False)
        .order_by('-location_updated_at')
    )
    users_without_pos = (
        User.objects
        .filter(last_lat__isnull=True)
        .order_by('-last_activity')[:50]
    )
    now = _tz.now()
    return render(request, 'admin_panel/positions.html', {
        'users_with_pos':    users_with_pos,
        'users_without_pos': users_without_pos,
        'nb_total':          User.objects.count(),
        'nb_avec_pos':       users_with_pos.count(),
        'now':               now,
    })


@_admin_required_view
def api_positions(request):
    """API JSON : positions actuelles de tous les utilisateurs."""
    from django.utils import timezone as tz
    now = tz.now()
    users = (
        User.objects
        .filter(last_lat__isnull=False, last_lng__isnull=False)
        .values(
            'id', 'first_name', 'last_name', 'telephone',
            'role', 'last_lat', 'last_lng', 'location_updated_at',
        )
    )
    data = []
    for u in users:
        updated = u['location_updated_at']
        age_s = int((now - updated).total_seconds()) if updated else None
        online = age_s is not None and age_s < 120
        data.append({
            'id':       u['id'],
            'nom':      f"{u['first_name']} {u['last_name']}".strip() or u['telephone'] or f"#{u['id']}",
            'role':     u['role'],
            'tel':      u['telephone'] or '',
            'lat':      float(u['last_lat']),
            'lng':      float(u['last_lng']),
            'age_s':    age_s,
            'online':   online,
            'updated':  updated.strftime('%H:%M:%S') if updated else '—',
        })
    return JsonResponse(data, safe=False)


@_admin_required_view
def api_position_trail(request, user_id):
    """API JSON : historique des positions d'un utilisateur (trail)."""
    from .models import UserPositionLog
    logs = (
        UserPositionLog.objects
        .filter(user_id=user_id)
        .order_by('-recorded_at')[:50]
    )
    trail = [
        {
            'lat': float(l.lat),
            'lng': float(l.lng),
            't':   l.recorded_at.strftime('%H:%M:%S'),
        }
        for l in logs
    ]
    trail.reverse()  # du plus ancien au plus récent
    return JsonResponse({'trail': trail})
