from django import forms
from .models import Boutique
from location.models import Ville, Commune, Quartier
from marche.models import Marche


_INPUT = 'w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 outline-none transition'
_SELECT = _INPUT + ' cursor-pointer'
_TEXTAREA = _INPUT + ' resize-y min-h-[80px]'


class BoutiqueForm(forms.ModelForm):
    class Meta:
        model  = Boutique
        fields = [
            'nom', 'telephone', 'description', 'logo',
            'ville', 'commune', 'quartier', 'marche',
            'type_commerce', 'adresse_exacte',
            'position',
        ]
        widgets = {
            'nom':           forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Nom de la boutique'}),
            'telephone':     forms.TextInput(attrs={'class': _INPUT, 'placeholder': '+242 06 000 0000'}),
            'description':   forms.Textarea(attrs={'class': _TEXTAREA, 'placeholder': 'Description de la boutique…'}),
            'adresse_exacte': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ex : Marché Total, Stand B-12'}),
            'type_commerce': forms.Select(attrs={'class': _SELECT}),
            'ville':         forms.Select(attrs={'class': _SELECT, 'id': 'id_ville'}),
            'commune':       forms.Select(attrs={'class': _SELECT, 'id': 'id_commune'}),
            'quartier':      forms.Select(attrs={'class': _SELECT, 'id': 'id_quartier'}),
            'marche':        forms.Select(attrs={'class': _SELECT, 'id': 'id_marche'}),
            'position':      forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ville'].queryset    = Ville.objects.filter(actif=True).order_by('nom')
        self.fields['commune'].queryset  = Commune.objects.filter(actif=True).order_by('nom')
        self.fields['quartier'].queryset = Quartier.objects.filter(actif=True).order_by('nom')
        self.fields['marche'].queryset   = Marche.objects.filter(actif=True).order_by('nom')
        self.fields['commune'].required  = False
        self.fields['quartier'].required = False
        self.fields['marche'].required   = False
        self.fields['ville'].required    = False
        self.fields['type_commerce'].required = False
        self.fields['description'].required   = False
        self.fields['telephone'].required     = False

    def clean(self):
        data = super().clean()
        # strip position text if empty string (HiddenInput may send '')
        pos = data.get('position')
        if not pos:
            data['position'] = None
        return data


class BoutiqueAdminForm(BoutiqueForm):
    """Formulaire admin avec champ user et raison_blocage."""
    class Meta(BoutiqueForm.Meta):
        fields = BoutiqueForm.Meta.fields + ['user', 'actif', 'raison_blocage']
        widgets = {
            **BoutiqueForm.Meta.widgets,
            'user':           forms.Select(attrs={'class': _SELECT}),
            'raison_blocage': forms.Textarea(attrs={'class': _TEXTAREA, 'placeholder': 'Raison du blocage…'}),
        }


# ── Geography forms ────────────────────────────────────────────────────────────

class VilleForm(forms.ModelForm):
    class Meta:
        model  = Ville
        fields = ['nom', 'pays', 'actif']
        widgets = {
            'nom':  forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Brazzaville'}),
            'pays': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Congo'}),
            'actif': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-emerald-600 rounded'}),
        }


class CommuneForm(forms.ModelForm):
    class Meta:
        model  = Commune
        fields = ['nom', 'ville', 'actif']
        widgets = {
            'nom':   forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Bacongo'}),
            'ville': forms.Select(attrs={'class': _SELECT}),
            'actif': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-emerald-600 rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ville'].queryset = Ville.objects.order_by('nom')


class QuartierForm(forms.ModelForm):
    class Meta:
        model  = Quartier
        fields = ['nom', 'commune', 'actif']
        widgets = {
            'nom':     forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Nom du quartier'}),
            'commune': forms.Select(attrs={'class': _SELECT}),
            'actif':   forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-emerald-600 rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['commune'].queryset = Commune.objects.select_related('ville').order_by('ville__nom', 'nom')


class MarcheForm(forms.ModelForm):
    class Meta:
        model  = Marche
        fields = ['nom', 'ville', 'commune', 'quartier', 'actif']
        widgets = {
            'nom':     forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Marché Total'}),
            'ville':   forms.Select(attrs={'class': _SELECT}),
            'commune': forms.Select(attrs={'class': _SELECT}),
            'quartier': forms.Select(attrs={'class': _SELECT}),
            'actif':   forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-emerald-600 rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ville'].queryset    = Ville.objects.order_by('nom')
        self.fields['commune'].queryset  = Commune.objects.select_related('ville').order_by('nom')
        self.fields['quartier'].queryset = Quartier.objects.select_related('commune').order_by('nom')
        self.fields['commune'].required  = False
        self.fields['quartier'].required = False
        self.fields['ville'].required    = False
