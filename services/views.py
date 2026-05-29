# views.py
from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Service, ServiceTexte, ServiceImage,Service

def services(request, category_slug=None):
    services = Service.objects.filter(actif=True)
    if category_slug:
        services = services.filter(category__slug=category_slug)
    return render(request, 'services/service.html', {'services': services})

def detail_service(request, slug):
    # ✅ Récupère le service consulté
    service = get_object_or_404(Service, slug=slug)

    # ✅ Récupère les textes et images associés
    textes = ServiceTexte.objects.filter(service=service).order_by('ordre')
    images = ServiceImage.objects.filter(service=service).order_by('ordre')

    # ✅ Autres services à afficher (exclut le service actuel)
    autres_services = (
        Service.objects.filter(actif=True)
        .exclude(id=service.id)
        .order_by('-populaire', 'nom')[:6]
    )

    return render(request, 'services/detail_service.html', {
        'service': service,
        'textes': textes,
        'images': images,
        'autres_services': autres_services,
    })


