import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from location.models import Ville
from .models import Produit, Categorie, Vendeur, Marche
from .forms import VendeurForm

User = get_user_model()


# ── Marketplace ───────────────────────────────────────────────────────────────

def accueil_marche(request):
    categories = Categorie.objects.all()
    produits   = Produit.objects.filter(disponibilite=True).select_related(
        'categorie', 'vendeur', 'marche', 'ville'
    )
    q        = request.GET.get('q', '')
    cat_slug = request.GET.get('cat', '')
    ville_id = request.GET.get('ville', '')

    if q:
        produits = produits.filter(Q(nom__icontains=q) | Q(description__icontains=q))
    if cat_slug:
        produits = produits.filter(categorie__slug=cat_slug)
    if ville_id:
        produits = produits.filter(ville_id=ville_id)

    return render(request, 'marche/accueil_marche.html', {
        'categories': categories,
        'produits':   produits[:60],
        'total':      produits.count(),
        'q':          q,
        'cat_slug':   cat_slug,
        'ville_id':   ville_id,
        'villes':     Ville.objects.filter(actif=True),
    })


def detail_produit(request, pk):
    produit   = get_object_or_404(Produit, pk=pk, disponibilite=True)
    images_qs = list(produit.images.select_related('couleur').order_by('ordre', 'date_ajout'))

    # Galerie unifiée : ProduitImage en premier, fallback sur produit.image
    gallery = []
    for img in images_qs:
        try:
            url = img.image.url
        except Exception:
            continue
        gallery.append({
            'pk':          img.pk,
            'url':         url,
            'principale':  img.principale,
            'description': img.description or '',
            'couleur_id':  img.couleur_id,
            'couleur_nom': img.couleur.nom      if img.couleur else None,
            'couleur_hex': img.couleur.code_hex if img.couleur else None,
        })

    # Fallback : pas de ProduitImage → utiliser produit.image
    if not gallery and produit.image:
        try:
            gallery = [{
                'pk':          None,
                'url':         produit.image.url,
                'principale':  True,
                'description': '',
                'couleur_id':  None,
                'couleur_nom': None,
                'couleur_hex': None,
            }]
        except Exception:
            pass

    # Couleurs uniques
    seen_c, couleurs = set(), []
    for img in images_qs:
        if img.couleur and img.couleur_id not in seen_c:
            couleurs.append(img.couleur)
            seen_c.add(img.couleur_id)

    # Image principale (principale=True ou première)
    main_image = next((i for i in gallery if i['principale']), gallery[0]) if gallery else None

    # Produits de la même catégorie
    if produit.categorie:
        autres = Produit.objects.filter(
            categorie=produit.categorie, disponibilite=True
        ).exclude(pk=pk).select_related('categorie', 'vendeur').prefetch_related('images')[:10]
    else:
        autres = []

    return render(request, 'marche/detail_produit.html', {
        'produit':    produit,
        'gallery':    gallery,
        'main_image': main_image,
        'images_data': json.dumps(gallery),   # pour le JS
        'couleurs':   couleurs,
        'autres':     autres,
    })


def panier(request):
    return render(request, 'marche/panier.html')


# ── API recherche utilisateurs ────────────────────────────────────────────────

@login_required
def api_users_search(request):
    """Retourne les utilisateurs correspondant à la recherche (nom ou téléphone)."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    users = User.objects.filter(
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q)  |
        Q(telephone__icontains=q)  |
        Q(username__icontains=q)
    ).filter(statut=True)[:15]
    data = [
        {
            'id':        u.pk,
            'nom':       f'{u.first_name} {u.last_name}'.strip() or u.username,
            'telephone': u.telephone or '—',
            'role':      u.get_role_display(),
            'initiales': (u.first_name[:1] + u.last_name[:1]).upper() or u.username[:2].upper(),
        }
        for u in users
    ]
    return JsonResponse(data, safe=False)


# ── CRUD Vendeurs ─────────────────────────────────────────────────────────────

@login_required
def vendeur_liste(request):
    vendeurs = Vendeur.objects.select_related(
        'user', 'ville', 'commune', 'quartier', 'marche'
    ).all()
    return render(request, 'marche/vendeur_liste.html', {'vendeurs': vendeurs})


@login_required
def vendeur_creer(request):
    if request.method == 'POST':
        form = VendeurForm(request.POST)
        if form.is_valid():
            vendeur = form.save()
            messages.success(request, f'Boutique « {vendeur.nom_boutique} » créée.')
            return redirect('marche:vendeur_liste')
        else:
            messages.error(request, 'Veuillez corriger les erreurs.')
    else:
        form = VendeurForm()
    return render(request, 'marche/vendeur_form.html', {
        'form': form, 'titre': 'Créer une boutique', 'action': 'creer',
    })


@login_required
def vendeur_modifier(request, pk):
    vendeur = get_object_or_404(Vendeur, pk=pk)
    if request.method == 'POST':
        form = VendeurForm(request.POST, instance=vendeur)
        if form.is_valid():
            form.save()
            messages.success(request, f'Boutique « {vendeur.nom_boutique} » mise à jour.')
            return redirect('marche:vendeur_liste')
        else:
            messages.error(request, 'Veuillez corriger les erreurs.')
    else:
        form = VendeurForm(instance=vendeur)
    return render(request, 'marche/vendeur_form.html', {
        'form': form, 'vendeur': vendeur,
        'titre': f'Modifier — {vendeur.nom_boutique}', 'action': 'modifier',
        'position_init': vendeur.position_geojson,
    })


@login_required
def vendeur_supprimer(request, pk):
    vendeur = get_object_or_404(Vendeur, pk=pk)
    if request.method == 'POST':
        nom = vendeur.nom_boutique
        vendeur.delete()
        messages.success(request, f'Boutique « {nom} » supprimée.')
    return redirect('marche:vendeur_liste')


# ── Vue publique inscription (redirige vers création admin) ───────────────────

def inscription_vendeur(request):
    """Point d'entrée public — redirige vers le formulaire de création vendeur."""
    return redirect('marche:vendeur_creer')


# ══════════════════════════════════════════════════════════════════════════════
#  API JSON — pour l'application mobile Flutter
# ══════════════════════════════════════════════════════════════════════════════

def _img_url(request, field):
    """Retourne l'URL absolue d'un ImageField ou None."""
    try:
        if field and field.name:
            return request.build_absolute_uri(field.url)
    except Exception:
        pass
    return None


def api_categories(request):
    cats = Categorie.objects.all()
    data = [{"id": c.pk, "nom": c.nom, "emoji": c.emoji, "slug": c.slug} for c in cats]
    return JsonResponse(data, safe=False)


def api_produits(request):
    qs = Produit.objects.filter(disponibilite=True).select_related('categorie', 'vendeur')
    q        = request.GET.get('q', '').strip()
    cat_slug = request.GET.get('cat', '').strip()
    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(description__icontains=q))
    if cat_slug:
        qs = qs.filter(categorie__slug=cat_slug)

    data = []
    for p in qs[:80]:
        data.append({
            "id":          str(p.pk),
            "nom":         p.nom,
            "description": p.description,
            "prix":        float(p.prix),
            "prix_promo":  float(p.prix_promo) if p.prix_promo else None,
            "devise":      p.devise,
            "unite":       p.unite,
            "stock":       p.stock,
            "image":       _img_url(request, p.image),
            "categorie":   {"id": p.categorie.pk, "nom": p.categorie.nom, "emoji": p.categorie.emoji} if p.categorie else None,
            "vendeur":     p.vendeur.nom_boutique if p.vendeur else None,
        })
    return JsonResponse(data, safe=False)


def api_produit_detail(request, pk):
    p = get_object_or_404(Produit, pk=pk, disponibilite=True)
    images = []
    for img in p.images.select_related('couleur').order_by('ordre', 'date_ajout'):
        try:
            images.append({
                "url":        request.build_absolute_uri(img.image.url),
                "principale": img.principale,
                "couleur":    img.couleur.nom if img.couleur else None,
                "couleur_hex": img.couleur.code_hex if img.couleur else None,
            })
        except Exception:
            pass
    if not images and p.image:
        try:
            images = [{"url": request.build_absolute_uri(p.image.url), "principale": True, "couleur": None, "couleur_hex": None}]
        except Exception:
            pass

    v = p.vendeur
    return JsonResponse({
        "id":          str(p.pk),
        "nom":         p.nom,
        "description": p.description,
        "prix":        float(p.prix),
        "prix_promo":  float(p.prix_promo) if p.prix_promo else None,
        "prix_actuel": float(p.prix_actuel),
        "remise_pct":  p.remise_pct,
        "devise":      p.devise,
        "unite":       p.unite,
        "stock":       p.stock,
        "disponibilite": p.disponibilite,
        "image":       _img_url(request, p.image),
        "images":      images,
        "categorie":   {"id": p.categorie.pk, "nom": p.categorie.nom} if p.categorie else None,
        "vendeur":     v.nom_boutique if v else None,
        "stand":       getattr(v, 'stand', None),
        "marche":      (v.marche.nom if v.marche else None) if v else None,
        "quartier":    (v.quartier.nom if v.quartier else None) if v else None,
        "commune":     (v.commune.nom if v.commune else None) if v else None,
        "ville":       p.ville.nom if p.ville else ((v.ville.nom if v.ville else None) if v else None),
    })
