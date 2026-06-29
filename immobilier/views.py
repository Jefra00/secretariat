import json
from datetime import date, datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST

from .models import Immobilier, ImmobilierCategory, DemandeVisite


# ── Helpers ───────────────────────────────────────────────────────────────────

def _img_url(request, img_field):
    try:
        return request.build_absolute_uri(img_field.url)
    except Exception:
        return None


# ── Page d'accueil immobilier ─────────────────────────────────────────────────

def accueil_immobilier(request):
    qs = Immobilier.objects.select_related('vendeur', 'categorie').prefetch_related('photos')

    q         = request.GET.get('q', '').strip()
    cat_id    = request.GET.get('cat', '')
    type_bien = request.GET.get('type', '')
    type_offre = request.GET.get('offre', '')
    ville     = request.GET.get('ville', '').strip()
    prix_max  = request.GET.get('prix_max', '').strip()
    meuble    = request.GET.get('meuble', '')

    if q:
        qs = qs.filter(
            Q(titre__icontains=q) | Q(description__icontains=q) |
            Q(ville__icontains=q) | Q(adresse__icontains=q)
        )
    if cat_id:
        qs = qs.filter(categorie_id=cat_id)
    if type_bien:
        qs = qs.filter(type_bien=type_bien)
    if type_offre:
        qs = qs.filter(type_offre=type_offre)
    if ville:
        qs = qs.filter(ville__icontains=ville)
    if prix_max:
        try:
            qs = qs.filter(prix__lte=float(prix_max))
        except ValueError:
            pass
    if meuble == '1':
        qs = qs.filter(meuble=True)

    qs = qs.filter(statut='disponible')

    categories = ImmobilierCategory.objects.all()
    total      = qs.count()

    return render(request, 'immobilier/accueil_immobilier.html', {
        'biens':      qs[:60],
        'total':      total,
        'categories': categories,
        'q':          q,
        'cat_id':     cat_id,
        'type_bien':  type_bien,
        'type_offre': type_offre,
        'ville':      ville,
        'prix_max':   prix_max,
        'meuble':     meuble,
        'TYPE_BIEN':  Immobilier.TYPE_BIEN,
        'TYPE_OFFRE': Immobilier.TYPE_OFFRE,
    })


# ── Page de détail ────────────────────────────────────────────────────────────

def detail_immobilier(request, pk):
    bien = get_object_or_404(
        Immobilier.objects.select_related('vendeur', 'categorie').prefetch_related('photos'),
        pk=pk,
    )

    gallery     = list(bien.photos.order_by('ordre', 'date_creation'))
    main_photo  = next((p for p in gallery if p.principale), gallery[0] if gallery else None)
    autres      = (
        Immobilier.objects
        .filter(type_bien=bien.type_bien, statut='disponible')
        .exclude(pk=bien.pk)
        .prefetch_related('photos')[:6]
    )

    visite_ok    = False
    demande      = None
    form_error   = None
    form_data    = {}

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f'/connexion/?next=/immobilier/bien/{pk}/')

        date_str  = request.POST.get('date_souhaitee', '').strip()
        heure_str = request.POST.get('heure_souhaitee', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        message   = request.POST.get('message', '').strip()
        form_data = request.POST.dict()

        if not date_str or not telephone:
            form_error = "La date souhaitée et le téléphone sont obligatoires."
        else:
            try:
                date_visite = date.fromisoformat(date_str)
                if date_visite < date.today():
                    raise ValueError("La date ne peut pas être dans le passé.")
                heure_visite = None
                if heure_str:
                    heure_visite = datetime.strptime(heure_str, '%H:%M').time()

                demande = DemandeVisite.objects.create(
                    bien=bien,
                    client=request.user,
                    date_souhaitee=date_visite,
                    heure_souhaitee=heure_visite,
                    telephone=telephone,
                    message=message,
                )
                visite_ok = True
            except ValueError as e:
                form_error = str(e) if str(e) else "Date invalide."

    return render(request, 'immobilier/detail_immobilier.html', {
        'bien':       bien,
        'gallery':    gallery,
        'main_photo': main_photo,
        'autres':     autres,
        'visite_ok':  visite_ok,
        'demande':    demande,
        'form_error': form_error,
        'form_data':  form_data,
        'today_str':  date.today().isoformat(),
    })


# ── Mes demandes de visite ────────────────────────────────────────────────────

def mes_visites(request):
    if not request.user.is_authenticated:
        return redirect('/connexion/?next=/immobilier/mes-visites/')
    demandes = (
        DemandeVisite.objects
        .filter(client=request.user)
        .select_related('bien')
        .prefetch_related('bien__photos')
    )
    return render(request, 'immobilier/mes_visites.html', {'demandes': demandes})


# ── API JSON (pour Flutter) ───────────────────────────────────────────────────

def api_biens(request):
    qs = (
        Immobilier.objects
        .select_related('vendeur', 'categorie')
        .prefetch_related('photos')
        .filter(statut='disponible')
    )

    q          = request.GET.get('q', '')
    cat        = request.GET.get('cat', '')
    type_bien  = request.GET.get('type', '')
    type_offre = request.GET.get('offre', '')
    ville      = request.GET.get('ville', '')

    if q:
        qs = qs.filter(Q(titre__icontains=q) | Q(ville__icontains=q) | Q(description__icontains=q))
    if cat:
        qs = qs.filter(categorie_id=cat)
    if type_bien:
        qs = qs.filter(type_bien=type_bien)
    if type_offre:
        qs = qs.filter(type_offre=type_offre)
    if ville:
        qs = qs.filter(ville__icontains=ville)

    data = []
    for b in qs[:60]:
        main_photo = b.photos.filter(principale=True).first() or b.photos.first()
        data.append({
            'id':           b.pk,
            'titre':        b.titre,
            'type_bien':    b.type_bien,
            'type_offre':   b.type_offre,
            'statut':       b.statut,
            'prix':         float(b.prix),
            'prix_actuel':  float(b.prix_actuel),
            'remise_pct':   b.remise_pct,
            'superficie':   float(b.superficie),
            'nombre_chambres': b.nombre_chambres,
            'nombre_salles_bain': b.nombre_salles_bain,
            'meuble':       b.meuble,
            'ville':        b.ville,
            'adresse':      b.adresse,
            'image':        _img_url(request, main_photo.image) if main_photo else None,
            'categorie':    {'id': b.categorie.pk, 'nom': str(b.categorie)} if b.categorie else None,
        })
    return JsonResponse(data, safe=False)


def api_bien_detail(request, pk):
    b = get_object_or_404(Immobilier, pk=pk, statut='disponible')
    photos = []
    for p in b.photos.order_by('ordre', 'date_creation'):
        try:
            photos.append({'url': request.build_absolute_uri(p.image.url), 'principale': p.principale})
        except Exception:
            pass

    return JsonResponse({
        'id':           b.pk,
        'titre':        b.titre,
        'type_bien':    b.type_bien,
        'type_offre':   b.type_offre,
        'statut':       b.statut,
        'prix':         float(b.prix),
        'prix_promotionnel': float(b.prix_promotionnel) if b.prix_promotionnel else None,
        'prix_actuel':  float(b.prix_actuel),
        'remise_pct':   b.remise_pct,
        'superficie':   float(b.superficie),
        'nombre_chambres':    b.nombre_chambres,
        'nombre_salles_bain': b.nombre_salles_bain,
        'nombre_salons':      b.nombre_salons,
        'nombre_cuisines':    b.nombre_cuisines,
        'nombre_garages':     b.nombre_garages,
        'etage':              b.etage,
        'annee_construction': b.annee_construction,
        'meuble':       b.meuble,
        'piscine':      b.piscine,
        'parking':      b.parking,
        'gardien':      b.gardien,
        'wifi':         b.wifi,
        'climatisation': b.climatisation,
        'generatrice':  b.generatrice,
        'eau_courante': b.eau_courante,
        'ville':        b.ville,
        'adresse':      b.adresse,
        'latitude':     float(b.latitude) if b.latitude else None,
        'longitude':    float(b.longitude) if b.longitude else None,
        'description':  b.description,
        'caution':      b.caution or '',
        'photos':       photos,
        'categorie':    {'id': b.categorie.pk, 'nom': str(b.categorie)} if b.categorie else None,
        'vendeur_tel':  b.vendeur.telephone if hasattr(b.vendeur, 'telephone') else None,
    })


@require_POST
def api_demande_visite(request, pk):
    bien = get_object_or_404(Immobilier, pk=pk, statut='disponible')
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentification requise.'}, status=401)
    try:
        data       = json.loads(request.body)
        date_str   = data.get('date_souhaitee', '')
        heure_str  = data.get('heure_souhaitee', '')
        telephone  = data.get('telephone', '').strip()
        message    = data.get('message', '')
        if not date_str or not telephone:
            return JsonResponse({'error': 'date_souhaitee et telephone sont obligatoires.'}, status=400)
        date_visite  = date.fromisoformat(date_str)
        heure_visite = datetime.strptime(heure_str, '%H:%M').time() if heure_str else None
        demande = DemandeVisite.objects.create(
            bien=bien, client=request.user,
            date_souhaitee=date_visite, heure_souhaitee=heure_visite,
            telephone=telephone, message=message,
        )
        return JsonResponse({'id': demande.pk, 'statut': demande.statut}, status=201)
    except (ValueError, KeyError) as e:
        return JsonResponse({'error': str(e)}, status=400)
