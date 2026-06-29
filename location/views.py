import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Ville, Commune, Quartier
from .forms import VilleForm, CommuneForm, QuartierForm


# ─── API cascade : communes et quartiers (utilisés par les formulaires) ────────

def api_communes(request):
    """Retourne les communes d'une ville en JSON."""
    ville_id = request.GET.get('ville_id')
    data = list(
        Commune.objects.filter(ville_id=ville_id, actif=True)
                       .order_by('nom')
                       .values('id', 'nom')
    )
    return JsonResponse(data, safe=False)


def api_quartiers(request):
    """Retourne les quartiers d'une commune en JSON."""
    commune_id = request.GET.get('commune_id')
    data = list(
        Quartier.objects.filter(commune_id=commune_id, actif=True)
                        .order_by('nom')
                        .values('id', 'nom')
    )
    return JsonResponse(data, safe=False)


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required
def liste(request):
    tab = request.GET.get('tab', 'villes')
    return render(request, 'location/liste.html', {
        'tab': tab,
        'villes':    Ville.objects.all(),
        'communes':  Commune.objects.select_related('ville').all(),
        'quartiers': Quartier.objects.select_related('commune__ville').all(),
        'nb_villes':    Ville.objects.count(),
        'nb_communes':  Commune.objects.count(),
        'nb_quartiers': Quartier.objects.count(),
    })


# ─── API GeoJSON (utilisé par la carte pour afficher les contours existants) ──

def api_geojson(request):
    features = []

    type_filtre = request.GET.get('type', 'all')

    if type_filtre in ('all', 'villes'):
        for v in Ville.objects.filter(contour__isnull=False):
            features.append({
                'type': 'Feature',
                'properties': {'nom': v.nom, 'type': 'ville', 'id': v.pk},
                'geometry': json.loads(v.contour.geojson),
            })

    if type_filtre in ('all', 'communes'):
        for c in Commune.objects.filter(contour__isnull=False).select_related('ville'):
            features.append({
                'type': 'Feature',
                'properties': {'nom': c.nom, 'ville': c.ville.nom, 'type': 'commune', 'id': c.pk},
                'geometry': json.loads(c.contour.geojson),
            })

    if type_filtre in ('all', 'quartiers'):
        for q in Quartier.objects.filter(contour__isnull=False).select_related('commune__ville'):
            features.append({
                'type': 'Feature',
                'properties': {'nom': q.nom, 'commune': q.commune.nom, 'type': 'quartier', 'id': q.pk},
                'geometry': json.loads(q.contour.geojson),
            })

    return JsonResponse({'type': 'FeatureCollection', 'features': features})


# ─── Helpers partagés ─────────────────────────────────────────────────────────

def _render_form(request, form, titre, type_entite, instance=None):
    ctx = {
        'form': form,
        'titre': titre,
        'type_entite': type_entite,
        'instance': instance,
        'position_init': instance.position_geojson if instance else None,
        'contour_init':  instance.contour_geojson  if instance else None,
    }
    return render(request, 'location/carte_form.html', ctx)


# ─── Villes ───────────────────────────────────────────────────────────────────

@login_required
def ville_creer(request):
    if request.method == 'POST':
        form = VilleForm(request.POST)
        if form.is_valid():
            v = form.save()
            messages.success(request, f'Ville « {v.nom} » enregistrée.')
            return redirect('location:liste')
    else:
        form = VilleForm()
    return _render_form(request, form, 'Ajouter une ville', 'ville')


@login_required
def ville_modifier(request, pk):
    ville = get_object_or_404(Ville, pk=pk)
    if request.method == 'POST':
        form = VilleForm(request.POST, instance=ville)
        if form.is_valid():
            form.save()
            messages.success(request, f'Ville « {ville.nom} » mise à jour.')
            return redirect('location:liste')
    else:
        form = VilleForm(instance=ville)
    return _render_form(request, form, f'Modifier — {ville.nom}', 'ville', ville)


@login_required
def ville_supprimer(request, pk):
    ville = get_object_or_404(Ville, pk=pk)
    if request.method == 'POST':
        nom = ville.nom
        ville.delete()
        messages.success(request, f'Ville « {nom} » supprimée.')
    return redirect('location:liste')


# ─── Communes ─────────────────────────────────────────────────────────────────

@login_required
def commune_creer(request):
    if request.method == 'POST':
        form = CommuneForm(request.POST)
        if form.is_valid():
            c = form.save()
            messages.success(request, f'Commune « {c.nom} » enregistrée.')
            return redirect('location:liste')
    else:
        form = CommuneForm()
    return _render_form(request, form, 'Ajouter une commune', 'commune')


@login_required
def commune_modifier(request, pk):
    commune = get_object_or_404(Commune, pk=pk)
    if request.method == 'POST':
        form = CommuneForm(request.POST, instance=commune)
        if form.is_valid():
            form.save()
            messages.success(request, f'Commune « {commune.nom} » mise à jour.')
            return redirect('location:liste')
    else:
        form = CommuneForm(instance=commune)
    return _render_form(request, form, f'Modifier — {commune.nom}', 'commune', commune)


@login_required
def commune_supprimer(request, pk):
    commune = get_object_or_404(Commune, pk=pk)
    if request.method == 'POST':
        nom = commune.nom
        commune.delete()
        messages.success(request, f'Commune « {nom} » supprimée.')
    return redirect('location:liste')


# ─── Quartiers ────────────────────────────────────────────────────────────────

@login_required
def quartier_creer(request):
    if request.method == 'POST':
        form = QuartierForm(request.POST)
        if form.is_valid():
            q = form.save()
            messages.success(request, f'Quartier « {q.nom} » enregistré.')
            return redirect('location:liste')
    else:
        form = QuartierForm()
    return _render_form(request, form, 'Ajouter un quartier', 'quartier')


@login_required
def quartier_modifier(request, pk):
    quartier = get_object_or_404(Quartier, pk=pk)
    if request.method == 'POST':
        form = QuartierForm(request.POST, instance=quartier)
        if form.is_valid():
            form.save()
            messages.success(request, f'Quartier « {quartier.nom} » mis à jour.')
            return redirect('location:liste')
    else:
        form = QuartierForm(instance=quartier)
    return _render_form(request, form, f'Modifier — {quartier.nom}', 'quartier', quartier)


@login_required
def quartier_supprimer(request, pk):
    quartier = get_object_or_404(Quartier, pk=pk)
    if request.method == 'POST':
        nom = quartier.nom
        quartier.delete()
        messages.success(request, f'Quartier « {nom} » supprimé.')
    return redirect('location:liste')
