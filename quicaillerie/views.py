from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import CategorieQuincaillerie, ProduitQuincaillerie


def accueil_quicaillerie(request):
    produits = ProduitQuincaillerie.objects.filter(statut='disponible').select_related('categorie', 'boutique').prefetch_related('images')
    categories = CategorieQuincaillerie.objects.filter(categorie_parent__isnull=True)

    q = request.GET.get('q', '').strip()
    cat_id = request.GET.get('cat', '')
    ville = request.GET.get('ville', '').strip()
    marque = request.GET.get('marque', '').strip()
    prix_max = request.GET.get('prix_max', '').strip()
    etat = request.GET.get('etat', '')
    promo_only = request.GET.get('promo', '')

    if q:
        produits = produits.filter(nom__icontains=q) | produits.filter(marque__icontains=q) | produits.filter(description__icontains=q)
        produits = produits.distinct()
    if cat_id:
        produits = produits.filter(categorie__pk=cat_id)
    if ville:
        produits = produits.filter(ville__icontains=ville)
    if marque:
        produits = produits.filter(marque__icontains=marque)
    if prix_max:
        try:
            produits = produits.filter(prix__lte=float(prix_max))
        except ValueError:
            pass
    if etat:
        produits = produits.filter(etat=etat)

    total = produits.count()

    if promo_only:
        produits = [p for p in produits if p.is_en_promo]
        total = len(produits)

    return render(request, 'quicaillerie/accueil_quicaillerie.html', {
        'produits': produits,
        'categories': categories,
        'total': total,
        'q': q,
        'cat_id': cat_id,
        'ville': ville,
        'marque': marque,
        'prix_max': prix_max,
        'etat': etat,
        'promo_only': promo_only,
        'ETAT_CHOICES': ProduitQuincaillerie.ETAT,
    })


def detail_quicaillerie(request, pk):
    produit = get_object_or_404(ProduitQuincaillerie, pk=pk)
    images = produit.images.all()
    similaires = ProduitQuincaillerie.objects.filter(
        categorie=produit.categorie,
        statut='disponible'
    ).exclude(pk=pk).select_related('categorie').prefetch_related('images')[:6]

    return render(request, 'quicaillerie/detail_quicaillerie.html', {
        'produit': produit,
        'images': images,
        'similaires': similaires,
    })


def panier_quicaillerie(request):
    from django.shortcuts import redirect
    return redirect('marche:panier')


# ── API ──────────────────────────────────────────────────────────────────────

def api_categories(request):
    cats = CategorieQuincaillerie.objects.all().order_by('nom')
    return JsonResponse(
        [{'id': c.pk, 'nom': c.nom, 'icone': c.icone} for c in cats],
        safe=False
    )


def api_produits(request):
    qs = ProduitQuincaillerie.objects.filter(statut='disponible').select_related('categorie', 'boutique').prefetch_related('images')
    data = []
    for p in qs:
        img = p.images.filter(principale=True).first() or p.images.first()
        data.append({
            'id': p.pk,
            'nom': p.nom,
            'marque': p.marque,
            'prix': float(p.prix),
            'prix_actuel': float(p.prix_actuel),
            'is_en_promo': p.is_en_promo,
            'remise_pct': p.remise_pct,
            'unite': p.unite,
            'ville': p.ville,
            'image': img.image.url if img else None,
        })
    return JsonResponse({'produits': data})


def api_produit_detail(request, pk):
    p = get_object_or_404(ProduitQuincaillerie, pk=pk)
    images = [{'url': i.image.url, 'principale': i.principale} for i in p.images.all()]
    return JsonResponse({
        'id': p.pk,
        'nom': p.nom,
        'reference': p.reference,
        'marque': p.marque,
        'prix': float(p.prix),
        'prix_actuel': float(p.prix_actuel),
        'is_en_promo': p.is_en_promo,
        'remise_pct': p.remise_pct,
        'description': p.description,
        'unite': p.unite,
        'etat': p.etat,
        'statut': p.statut,
        'garantie': p.garantie,
        'poids': float(p.poids) if p.poids else None,
        'livraison_disponible': p.livraison_disponible,
        'ville': p.ville,
        'adresse': p.adresse,
        'images': images,
        'categorie': {'id': p.categorie.pk, 'nom': p.categorie.nom} if p.categorie else None,
        'boutique': str(p.boutique) if p.boutique else None,
    })
