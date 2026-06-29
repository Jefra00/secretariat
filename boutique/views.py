import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.gis.geos import Point

from .models import Boutique
from .forms import (
    BoutiqueForm, BoutiqueAdminForm,
    VilleForm, CommuneForm, QuartierForm, MarcheForm,
)
from location.models import Ville, Commune, Quartier
from marche.models import Marche


def _is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')


def _admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(request, *args, **kwargs):
        if not _is_admin(request.user):
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect('connexion_client')
        return fn(request, *args, **kwargs)
    return wrapper


def _vendeur_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('vendeur_connexion')
        if request.user.role != 'vendeur':
            messages.error(request, "Accès réservé aux vendeurs.")
            return redirect('connexion_client')
        return fn(request, *args, **kwargs)
    return wrapper


def _parse_point(request):
    lat = request.POST.get('lat', '').strip()
    lng = request.POST.get('lng', '').strip()
    if lat and lng:
        try:
            return Point(float(lng), float(lat), srid=4326)
        except (ValueError, TypeError):
            pass
    return None


def _villes_json():
    villes = Ville.objects.filter(actif=True).values('id', 'nom', 'position')
    result = []
    for v in villes:
        pos = v.get('position')
        result.append({
            'id': v['id'],
            'nom': v['nom'],
            'lat': pos.y if pos else None,
            'lng': pos.x if pos else None,
        })
    return json.dumps(result)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — Géographie
# ══════════════════════════════════════════════════════════════════════════════

@_admin_required
def admin_geo(request):
    return render(request, 'boutique/admin/geo.html', {
        'nb_villes':    Ville.objects.count(),
        'nb_communes':  Commune.objects.count(),
        'nb_quartiers': Quartier.objects.count(),
        'nb_marches':   Marche.objects.count(),
    })


@_admin_required
def admin_villes(request):
    q = request.GET.get('q', '').strip()
    villes = Ville.objects.order_by('nom')
    if q:
        villes = villes.filter(nom__icontains=q)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'creer':
            form = VilleForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.position = _parse_point(request)
                obj.save()
                messages.success(request, "Ville créée.")
                return redirect('admin_villes')
        elif action == 'toggle':
            v = get_object_or_404(Ville, pk=request.POST.get('pk'))
            v.actif = not v.actif
            v.save(update_fields=['actif'])
            return redirect('admin_villes')
        elif action == 'supprimer':
            v = get_object_or_404(Ville, pk=request.POST.get('pk'))
            v.delete()
            messages.success(request, "Ville supprimée.")
            return redirect('admin_villes')
    else:
        form = VilleForm()

    return render(request, 'boutique/admin/villes.html', {'villes': villes, 'form': form, 'q': q})


@_admin_required
def admin_communes(request):
    q = request.GET.get('q', '').strip()
    ville_id = request.GET.get('ville', '')
    communes = Commune.objects.select_related('ville').order_by('ville__nom', 'nom')
    if q:
        communes = communes.filter(nom__icontains=q)
    if ville_id:
        communes = communes.filter(ville_id=ville_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'creer':
            form = CommuneForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.position = _parse_point(request)
                obj.save()
                messages.success(request, "Commune créée.")
                return redirect('admin_communes')
        elif action == 'toggle':
            c = get_object_or_404(Commune, pk=request.POST.get('pk'))
            c.actif = not c.actif
            c.save(update_fields=['actif'])
            return redirect('admin_communes')
        elif action == 'supprimer':
            c = get_object_or_404(Commune, pk=request.POST.get('pk'))
            c.delete()
            messages.success(request, "Commune supprimée.")
            return redirect('admin_communes')
    else:
        form = CommuneForm()

    return render(request, 'boutique/admin/communes.html', {
        'communes': communes, 'form': form, 'q': q,
        'villes': Ville.objects.order_by('nom'),
        'ville_filter': ville_id,
    })


@_admin_required
def admin_quartiers(request):
    q = request.GET.get('q', '').strip()
    commune_id = request.GET.get('commune', '')
    quartiers = Quartier.objects.select_related('commune', 'commune__ville').order_by('nom')
    if q:
        quartiers = quartiers.filter(nom__icontains=q)
    if commune_id:
        quartiers = quartiers.filter(commune_id=commune_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'creer':
            form = QuartierForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.position = _parse_point(request)
                obj.save()
                messages.success(request, "Quartier créé.")
                return redirect('admin_quartiers')
        elif action == 'toggle':
            q_obj = get_object_or_404(Quartier, pk=request.POST.get('pk'))
            q_obj.actif = not q_obj.actif
            q_obj.save(update_fields=['actif'])
            return redirect('admin_quartiers')
        elif action == 'supprimer':
            q_obj = get_object_or_404(Quartier, pk=request.POST.get('pk'))
            q_obj.delete()
            messages.success(request, "Quartier supprimé.")
            return redirect('admin_quartiers')
    else:
        form = QuartierForm()

    return render(request, 'boutique/admin/quartiers.html', {
        'quartiers': quartiers, 'form': form, 'q': q,
        'communes': Commune.objects.select_related('ville').order_by('nom'),
        'commune_filter': commune_id,
    })


@_admin_required
def admin_marches(request):
    q = request.GET.get('q', '').strip()
    marches = Marche.objects.select_related('ville', 'commune').order_by('nom')
    if q:
        marches = marches.filter(nom__icontains=q)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'creer':
            form = MarcheForm(request.POST)
            if form.is_valid():
                marche = form.save(commit=False)
                pos = _parse_point(request)
                if pos:
                    marche.position = pos
                marche.save()
                messages.success(request, "Marché créé.")
                return redirect('admin_marches')
        elif action == 'toggle':
            m = get_object_or_404(Marche, pk=request.POST.get('pk'))
            m.actif = not m.actif
            m.save(update_fields=['actif'])
            return redirect('admin_marches')
        elif action == 'supprimer':
            m = get_object_or_404(Marche, pk=request.POST.get('pk'))
            m.delete()
            messages.success(request, "Marché supprimé.")
            return redirect('admin_marches')
    else:
        form = MarcheForm()

    return render(request, 'boutique/admin/marches.html', {'marches': marches, 'form': form, 'q': q})


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — Boutiques
# ══════════════════════════════════════════════════════════════════════════════

@_admin_required
def admin_boutiques_list(request):
    q = request.GET.get('q', '').strip()
    statut = request.GET.get('statut', '')
    boutiques = Boutique.objects.select_related('user', 'ville', 'commune').order_by('-cree_le')
    if q:
        boutiques = boutiques.filter(
            Q(nom__icontains=q) | Q(user__first_name__icontains=q) | Q(user__telephone__icontains=q)
        )
    if statut == 'active':
        boutiques = boutiques.filter(actif=True)
    elif statut == 'bloquee':
        boutiques = boutiques.filter(actif=False)

    paginator = Paginator(boutiques, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'boutique/admin/boutiques_list.html', {
        'page_obj': page_obj, 'q': q, 'statut_filter': statut,
    })


@_admin_required
def admin_boutique_creer(request):
    from users.models import User
    if request.method == 'POST':
        form = BoutiqueAdminForm(request.POST, request.FILES)
        if form.is_valid():
            b = form.save(commit=False)
            pos = _parse_point(request)
            if pos:
                b.position = pos
            b.save()
            messages.success(request, f"Boutique « {b.nom} » créée.")
            return redirect('admin_boutiques_list')
    else:
        form = BoutiqueAdminForm()
    form.fields['user'].queryset = User.objects.filter(role='vendeur').order_by('first_name')
    return render(request, 'boutique/admin/boutique_form.html', {
        'form': form, 'titre': 'Créer une boutique', 'villes_json': _villes_json(),
    })


@_admin_required
def admin_boutique_modifier(request, pk):
    from users.models import User
    boutique = get_object_or_404(Boutique, pk=pk)
    if request.method == 'POST':
        form = BoutiqueAdminForm(request.POST, request.FILES, instance=boutique)
        if form.is_valid():
            b = form.save(commit=False)
            pos = _parse_point(request)
            if pos:
                b.position = pos
            b.save()
            messages.success(request, "Boutique mise à jour.")
            return redirect('admin_boutiques_list')
    else:
        form = BoutiqueAdminForm(instance=boutique)
    form.fields['user'].queryset = User.objects.filter(role='vendeur').order_by('first_name')
    return render(request, 'boutique/admin/boutique_form.html', {
        'form': form, 'boutique': boutique,
        'titre': f'Modifier — {boutique.nom}', 'villes_json': _villes_json(),
    })


@_admin_required
def admin_boutique_toggle(request, pk):
    boutique = get_object_or_404(Boutique, pk=pk)
    if request.method == 'POST':
        boutique.actif = not boutique.actif
        raison = request.POST.get('raison', '').strip()
        boutique.raison_blocage = raison if not boutique.actif else ''
        boutique.save(update_fields=['actif', 'raison_blocage'])
        action = "activée" if boutique.actif else "bloquée"
        messages.success(request, f"Boutique « {boutique.nom} » {action}.")
    return redirect('admin_boutiques_list')


# ══════════════════════════════════════════════════════════════════════════════
# VENDEUR — Ses boutiques
# ══════════════════════════════════════════════════════════════════════════════

@_vendeur_required
def vendeur_mes_boutiques(request):
    boutiques = (
        Boutique.objects
        .filter(user=request.user)
        .select_related('ville', 'commune', 'quartier', 'marche')
        .order_by('-cree_le')
    )
    return render(request, 'boutique/vendeur/mes_boutiques.html', {'boutiques': boutiques})


@_vendeur_required
def vendeur_boutique_creer(request):
    if request.method == 'POST':
        form = BoutiqueForm(request.POST, request.FILES)
        if form.is_valid():
            b = form.save(commit=False)
            b.user = request.user
            pos = _parse_point(request)
            if pos:
                b.position = pos
            b.save()
            messages.success(request, f"Boutique « {b.nom} » créée !")
            return redirect('vendeur_mes_boutiques')
    else:
        form = BoutiqueForm()
    return render(request, 'boutique/vendeur/boutique_form.html', {
        'form': form, 'titre': 'Nouvelle boutique', 'villes_json': _villes_json(),
    })


@_vendeur_required
def vendeur_boutique_modifier(request, pk):
    boutique = get_object_or_404(Boutique, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BoutiqueForm(request.POST, request.FILES, instance=boutique)
        if form.is_valid():
            b = form.save(commit=False)
            pos = _parse_point(request)
            if pos:
                b.position = pos
            b.save()
            messages.success(request, "Boutique mise à jour.")
            return redirect('vendeur_mes_boutiques')
    else:
        form = BoutiqueForm(instance=boutique)
    return render(request, 'boutique/vendeur/boutique_form.html', {
        'form': form, 'boutique': boutique,
        'titre': f'Modifier — {boutique.nom}', 'villes_json': _villes_json(),
    })


# ── AJAX ──────────────────────────────────────────────────────────────────────

def communes_par_ville(request, ville_id):
    data = list(Commune.objects.filter(ville_id=ville_id, actif=True).values('id', 'nom').order_by('nom'))
    return JsonResponse({'communes': data})


def quartiers_par_commune(request, commune_id):
    data = list(Quartier.objects.filter(commune_id=commune_id, actif=True).values('id', 'nom').order_by('nom'))
    return JsonResponse({'quartiers': data})


def marches_par_commune(request, commune_id):
    data = list(Marche.objects.filter(commune_id=commune_id, actif=True).values('id', 'nom').order_by('nom'))
    return JsonResponse({'marches': data})
