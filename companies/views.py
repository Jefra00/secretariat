from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Company, CompanyService
from services.models import Service


# 🏢 Liste des entreprises
@login_required
def company_list(request):
    companies = Company.objects.filter(actif=True)
    return render(request, "company/company_list.html", {"companies": companies})


# 📋 Détail d’une entreprise
@login_required
def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    services = company.services_personnalises.select_related("service")
    return render(request, "company/company_detail.html", {
        "company": company,
        "services": services,
    })


# ➕ Créer une entreprise
@login_required
def company_create(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        secteur = request.POST.get("secteur")
        email = request.POST.get("email")
        telephone = request.POST.get("telephone")
        adresse = request.POST.get("adresse")
        site_web = request.POST.get("site_web")

        company = Company.objects.create(
            nom=nom,
            secteur=secteur,
            email_contact=email,
            telephone=telephone,
            adresse=adresse,
            site_web=site_web,
        )
        messages.success(request, f"✅ L’entreprise « {company.nom} » a été ajoutée avec succès.")
        return redirect("company:company_detail", pk=company.pk)
    return render(request, "company/company_form.html")


# 🔄 Activer / désactiver une entreprise
@login_required
def company_toggle_status(request, pk):
    company = get_object_or_404(Company, pk=pk)
    company.actif = not company.actif
    company.save(update_fields=["actif"])
    messages.info(request, f"⚙️ Le statut de {company.nom} a été mis à jour.")
    return redirect("company:company_detail", pk=company.pk)


# 💼 Ajouter un service personnalisé à une entreprise
@login_required
def add_company_service(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    services = Service.objects.all()

    if request.method == "POST":
        service_id = request.POST.get("service")
        forfait = request.POST.get("forfait")
        tarif = request.POST.get("tarif")
        description = request.POST.get("description")

        service = get_object_or_404(Service, id=service_id)

        CompanyService.objects.create(
            company=company,
            service=service,
            forfait=forfait,
            tarif_personnalise=tarif or None,
            description_forfait=description,
        )

        messages.success(request, f"💼 Service « {service.nom} » ajouté à {company.nom}.")
        return redirect("company:company_detail", pk=company.pk)

    return render(request, "company/company_service_form.html", {
        "company": company,
        "services": services,
    })


# 🧾 Liste des services personnalisés
@login_required
def company_service_list(request):
    services = CompanyService.objects.select_related("company", "service")
    return render(request, "company/company_service_list.html", {"services": services})
