from django import forms
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry
from location.models import Ville, Commune, Quartier
from .models import Vendeur, TypeCommerce

User = get_user_model()


class VendeurForm(forms.ModelForm):
    """Crée ou modifie un vendeur en sélectionnant un utilisateur existant."""

    # Sélection de l'utilisateur existant
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(statut=True).order_by('first_name', 'last_name'),
        label='Utilisateur',
        empty_label='— Sélectionner un utilisateur —',
    )

    # Localisation (FKs cascade)
    ville    = forms.ModelChoiceField(
        queryset=Ville.objects.filter(actif=True).order_by('nom'),
        label='Ville', empty_label='— Choisir une ville —', required=False,
    )
    commune  = forms.ModelChoiceField(
        queryset=Commune.objects.none(),
        label='Commune', empty_label='— Choisir une commune —', required=False,
    )
    quartier = forms.ModelChoiceField(
        queryset=Quartier.objects.none(),
        label='Quartier', empty_label='— Choisir un quartier —', required=False,
    )

    position_json = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model  = Vendeur
        fields = [
            'user', 'nom_boutique', 'type_commerce',
            'ville', 'commune', 'quartier',
            'marche', 'nom_marche', 'stand',
            'description', 'actif',
        ]
        widgets = {
            'nom_boutique': forms.TextInput(attrs={'placeholder': 'Ex : Chez Mama Céleste'}),
            'nom_marche':   forms.TextInput(attrs={'placeholder': 'Ex : Marché Total'}),
            'stand':        forms.TextInput(attrs={'placeholder': 'Ex : Stand B12'}),
            'description':  forms.Textarea(attrs={'rows': 3, 'placeholder': 'Description de la boutique…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Recharge commune/quartier après POST ou lors d'une édition
        instance = kwargs.get('instance')
        if 'ville' in self.data:
            try:
                self.fields['commune'].queryset = Commune.objects.filter(
                    ville_id=int(self.data['ville']), actif=True
                ).order_by('nom')
            except (ValueError, TypeError):
                pass
        elif instance and instance.ville_id:
            self.fields['commune'].queryset = Commune.objects.filter(
                ville=instance.ville, actif=True
            ).order_by('nom')

        if 'commune' in self.data:
            try:
                self.fields['quartier'].queryset = Quartier.objects.filter(
                    commune_id=int(self.data['commune']), actif=True
                ).order_by('nom')
            except (ValueError, TypeError):
                pass
        elif instance and instance.commune_id:
            self.fields['quartier'].queryset = Quartier.objects.filter(
                commune=instance.commune, actif=True
            ).order_by('nom')

    def save(self, commit=True):
        instance = super().save(commit=False)
        pos_json = self.cleaned_data.get('position_json', '').strip()
        if pos_json:
            instance.position = GEOSGeometry(pos_json, srid=4326)
        if commit:
            instance.save()
        return instance


# Alias conservé pour la vue d'inscription publique (formulaire simplifié)
InscriptionVendeurForm = VendeurForm
