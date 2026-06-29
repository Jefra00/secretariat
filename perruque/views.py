import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Category, WigProduct


def perruque_accueil(request):
    categories = Category.objects.filter(parent=None)
    products = (
        WigProduct.objects
        .filter(status='available')
        .select_related('shop', 'shop__user', 'category')
        .prefetch_related('images__couleur')
    )

    q        = request.GET.get('q', '')
    cat_id   = request.GET.get('cat', '')
    texture  = request.GET.get('texture', '')
    material = request.GET.get('material', '')

    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(color__icontains=q)
        )
    if cat_id:
        try:
            products = products.filter(category_id=int(cat_id))
        except (ValueError, TypeError):
            pass
    if texture:
        products = products.filter(texture=texture)
    if material:
        products = products.filter(material=material)

    total = products.count()

    return render(request, 'perruque/perruque_accueil.html', {
        'categories': categories,
        'products':   products[:60],
        'total':      total,
        'q':          q,
        'cat_id':     cat_id,
        'texture':    texture,
        'material':   material,
        'textures':   WigProduct.TEXTURE_CHOICES,
        'materials':  WigProduct.MATERIAL_CHOICES,
    })


def detail_perruque(request, pk):
    product = get_object_or_404(WigProduct, pk=pk, status='available')

    images_qs = list(
        product.images
        .select_related('couleur')
        .prefetch_related('tailles')
        .order_by('ordre', 'date_ajout')
    )

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
            'tailles':     [{'pk': t.pk, 'nom': t.nom} for t in img.tailles.all()],
        })

    main_image = next((i for i in gallery if i['principale']), gallery[0]) if gallery else None

    seen_c, couleurs = set(), []
    for img in images_qs:
        if img.couleur and img.couleur_id not in seen_c:
            couleurs.append(img.couleur)
            seen_c.add(img.couleur_id)

    seen_t, tailles = set(), []
    for img in images_qs:
        for t in img.tailles.all():
            if t.pk not in seen_t:
                tailles.append(t)
                seen_t.add(t.pk)

    base_qs = (
        WigProduct.objects.filter(status='available')
        .exclude(pk=pk)
        .select_related('category', 'shop')
        .prefetch_related('images')
    )
    if product.category:
        cat_autres = list(base_qs.filter(category=product.category)[:10])
    else:
        cat_autres = []

    if len(cat_autres) < 10:
        excl = [p.pk for p in cat_autres] + [pk]
        fill = list(base_qs.exclude(pk__in=excl)[:10 - len(cat_autres)])
        autres = cat_autres + fill
    else:
        autres = cat_autres

    return render(request, 'perruque/detail_perruque.html', {
        'product':     product,
        'gallery':     gallery,
        'main_image':  main_image,
        'images_data': json.dumps(gallery, default=str),
        'couleurs':    couleurs,
        'tailles':     tailles,
        'autres':      autres,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  API JSON — pour l'application mobile Flutter
# ══════════════════════════════════════════════════════════════════════════════

from django.http import JsonResponse
from django.db.models import Q

def _img_url(request, field):
    try:
        if field and field.name:
            return request.build_absolute_uri(field.url)
    except Exception:
        pass
    return None


def api_categories_perruque(request):
    from .models import Category
    cats = Category.objects.filter(parent=None).order_by('name')
    data = [{"id": c.pk, "nom": c.name, "icon": c.icon} for c in cats]
    return JsonResponse(data, safe=False)


def api_produits_perruque(request):
    from .models import WigProduct
    qs = (WigProduct.objects
          .filter(status='available')
          .select_related('shop', 'category')
          .prefetch_related('images'))
    q        = request.GET.get('q', '').strip()
    cat      = request.GET.get('cat', '').strip()
    texture  = request.GET.get('texture', '').strip()
    material = request.GET.get('material', '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if cat:
        try:
            qs = qs.filter(category_id=int(cat))
        except ValueError:
            pass
    if texture:
        qs = qs.filter(texture=texture)
    if material:
        qs = qs.filter(material=material)

    data = []
    for p in qs[:80]:
        main_img = p.images.filter(principale=True).first() or p.images.first()
        data.append({
            "id":       p.pk,
            "nom":      p.name,
            "description": p.description if hasattr(p, 'description') else "",
            "prix":     float(p.price),
            "prix_promo": float(p.promotional_price) if p.promotional_price else None,
            "stock":    p.stock,
            "material": p.get_material_display() if hasattr(p, 'get_material_display') else p.material,
            "texture":  p.get_texture_display() if hasattr(p, 'get_texture_display') else p.texture,
            "image":    _img_url(request, main_img.image) if main_img else None,
            "categorie": {"id": p.category.pk, "nom": p.category.name} if p.category else None,
            "shop":     p.shop.name if p.shop else None,
        })
    return JsonResponse(data, safe=False)


def api_produit_detail_perruque(request, pk):
    from .models import WigProduct
    from django.shortcuts import get_object_or_404
    p = get_object_or_404(WigProduct, pk=pk, status='available')
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

    return JsonResponse({
        "id":          p.pk,
        "nom":         p.name,
        "description": p.description,
        "prix":        float(p.price),
        "prix_promo":  float(p.promotional_price) if p.promotional_price else None,
        "prix_actuel": float(p.prix_actuel),
        "remise_pct":  p.remise_pct,
        "stock":       p.stock,
        "status":      p.status,
        "material":    p.get_material_display(),
        "texture":     p.get_texture_display(),
        "color":       p.color,
        "length":      p.length,
        "city":        p.city,
        "location":    p.location,
        "delivery_available": p.delivery_available,
        "average_rating":     float(p.average_rating),
        "reviews_count":      p.reviews_count,
        "images":      images,
        "categorie":   {"id": p.category.pk, "nom": p.category.name} if p.category else None,
        "shop":        p.shop.name if p.shop else None,
    })
