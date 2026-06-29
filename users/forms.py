from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib.auth.forms import UserChangeForm
from .models import User, VendeurProfile


# ── CSS helpers ───────────────────────────────────────────────────────────────
_INPUT  = 'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none'
_SELECT = _INPUT + ' cursor-pointer'
_TEXTAREA = _INPUT + ' resize-none'


_FIELD_CLS = (
    'w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm '
    'focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 outline-none transition'
)


class ClientLoginForm(forms.Form):
    telephone = forms.CharField(
        label="Numéro de téléphone",
        widget=forms.TextInput(attrs={
            'placeholder': '+242 06 000 00 00',
            'class': _FIELD_CLS,
            'inputmode': 'tel',
            'autocomplete': 'tel',
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': _FIELD_CLS,
            'autocomplete': 'current-password',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        telephone = cleaned_data.get('telephone', '').replace(' ', '').replace('-', '')
        password  = cleaned_data.get('password')

        if telephone and password:
            from django.contrib.auth import authenticate as _auth
            user = _auth(None, telephone=telephone, password=password)
            if user is None:
                raise forms.ValidationError("Numéro de téléphone ou mot de passe incorrect.")
            if not user.statut:
                raise forms.ValidationError("Ce compte est désactivé. Contactez le support.")
            self.user = user
        return cleaned_data

    def get_user(self):
        return self.user

class UserCreationForm(DjangoUserCreationForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'telephone',
            'pays',
            'adresse',
            'role',
            'password1',
            'password2',
        ]
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'email': 'Adresse e-mail',
            'telephone': 'Téléphone',
            'pays': 'Pays',
            'adresse': 'Adresse',
            'role': 'Rôle',
            'password1': 'Mot de passe',
            'password2': 'Confirmer le mot de passe',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Style uniforme pour tous les champs
        base_classes = (
            'w-full rounded-lg border-slate-300 dark:border-slate-700 '
            'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
        )

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = base_classes
            field.widget.attrs['placeholder'] = field.label

        # Optionnel : masquer le champ "role" si l'utilisateur n'est pas superadmin
        request = kwargs.get('request')
        if request and not request.user.is_superuser:
            self.fields['role'].widget = forms.HiddenInput()
            self.fields['role'].initial = 'employe'


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'telephone', 'adresse',
            'pays', 'bio', 'avatar', 'langue', 'role'
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            for field_name in list(self.fields.keys()):
                if getattr(user, field_name, None):
                    self.fields.pop(field_name, None)

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full rounded-md border border-slate-300 dark:border-slate-700 bg-background-light dark:bg-background-dark p-2',
                'placeholder': field.label
            })

class UserUpdateForm(UserChangeForm):
    password = None  # On retire le champ mot de passe du formulaire de profil

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'telephone', 'pays',
            'adresse', 'bio', 'avatar', 'langue'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary',
                'placeholder': 'Prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary',
                'placeholder': 'Nom'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary',
                'placeholder': 'Adresse e-mail'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary',
                'placeholder': 'Téléphone'
            }),
            'pays': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary',
                'placeholder': 'Pays'
            }),
            'adresse': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary',
                'placeholder': 'Adresse'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary',
                'rows': 3,
                'placeholder': 'Quelques mots sur vous...'
            }),
            'langue': forms.Select(attrs={
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
            }),
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
            }),
        }


# ══════════════════════════════════════════════════════════════════════════════
# VENDEUR — Connexion
# ══════════════════════════════════════════════════════════════════════════════
class VendeurLoginForm(forms.Form):
    username = forms.CharField(
        label="Identifiant (email ou téléphone)",
        widget=forms.TextInput(attrs={'placeholder': 'Votre identifiant', 'class': _INPUT}),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': _INPUT}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = None

    def clean(self):
        cd = super().clean()
        username = cd.get('username', '').lower().strip()
        password = cd.get('password', '')
        if not username or not password:
            return cd
        # Try email first, then username directly
        try:
            u = User.objects.get(email=username)
            username = u.username
        except User.DoesNotExist:
            pass
        user = authenticate(username=username, password=password)
        if user is None:
            raise forms.ValidationError("Identifiant ou mot de passe incorrect.")
        if not user.statut:
            raise forms.ValidationError("Ce compte est désactivé.")
        if user.role != 'vendeur':
            raise forms.ValidationError("Ce compte n'est pas un compte vendeur.")
        self._user = user
        return cd

    def get_user(self):
        return self._user


# ══════════════════════════════════════════════════════════════════════════════
# VENDEUR — Création par admin (User + VendeurProfile en un seul form)
# ══════════════════════════════════════════════════════════════════════════════
class VendeurCreationForm(forms.ModelForm):
    """Enregistrement simplifié : compte vendeur uniquement, sans boutique."""
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': _INPUT, 'placeholder': '••••••••'}),
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={'class': _INPUT, 'placeholder': '••••••••'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'telephone', 'email']
        labels = {
            'first_name': "Nom complet",
            'telephone':  "Téléphone (utilisé pour la connexion)",
            'email':      "Email (optionnel)",
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Nom et prénom'}),
            'telephone':  forms.TextInput(attrs={'class': _INPUT, 'placeholder': '+242 06 000 0000'}),
            'email':      forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'email@exemple.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False

    def clean_telephone(self):
        phone = self.cleaned_data.get('telephone', '').replace(' ', '').replace('-', '')
        if not phone:
            raise forms.ValidationError("Le numéro de téléphone est obligatoire.")
        if User.objects.filter(telephone=phone).exists():
            raise forms.ValidationError("Un compte existe déjà avec ce numéro.")
        return phone

    def clean(self):
        data = super().clean()
        p1, p2 = data.get('password1', ''), data.get('password2', '')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Les mots de passe ne correspondent pas.")
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        phone = self.cleaned_data['telephone']
        user.username = phone
        user.telephone = phone
        user.role = 'vendeur'
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


# ══════════════════════════════════════════════════════════════════════════════
# VENDEUR — Modifier son profil
# ══════════════════════════════════════════════════════════════════════════════
class VendeurProfileForm(forms.ModelForm):
    class Meta:
        model = VendeurProfile
        fields = ['nom_commercial', 'description', 'logo', 'telephone_pro', 'email_pro', 'site_web']
        widgets = {
            'nom_commercial': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Nom de votre boutique'}),
            'description':    forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 4, 'placeholder': 'Décrivez votre activité…'}),
            'logo':           forms.ClearableFileInput(attrs={'class': _INPUT}),
            'telephone_pro':  forms.TextInput(attrs={'class': _INPUT, 'placeholder': '+242…'}),
            'email_pro':      forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'contact@ma-boutique.com'}),
            'site_web':       forms.URLInput(attrs={'class': _INPUT, 'placeholder': 'https://…'}),
        }


# ══════════════════════════════════════════════════════════════════════════════
# PRODUITS PAR SECTION
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# FORMULAIRES PRODUITS — un par section, champs corrects, save corrigé
# ══════════════════════════════════════════════════════════════════════════════

def _slug_unique(Model, base_slug):
    """Génère un slug unique pour les modèles qui en ont besoin."""
    from django.utils.text import slugify
    import uuid as _uuid
    slug = slugify(base_slug) or _uuid.uuid4().hex[:8]
    if Model.objects.filter(slug=slug).exists():
        slug = f'{slug}-{_uuid.uuid4().hex[:6]}'
    return slug


class ProduitRestoForm(forms.Form):
    """Plat (Dish) pour un vendeur RESTO."""
    title             = forms.CharField(label="Nom du plat", widget=forms.TextInput(attrs={'class': _INPUT}))
    description       = forms.CharField(label="Description", required=False, widget=forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}))
    base_price        = forms.DecimalField(label="Prix de base (FCFA)", min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    base_time_minutes = forms.IntegerField(label="Temps de préparation (min)", min_value=0, initial=20, widget=forms.NumberInput(attrs={'class': _INPUT}))
    image             = forms.URLField(label="URL image", required=False, widget=forms.URLInput(attrs={'class': _INPUT, 'placeholder': 'https://…'}))
    active            = forms.BooleanField(label="Actif", required=False, initial=True)

    def save_for_restaurant(self, restaurant):
        from resto.models import Dish
        title = self.cleaned_data['title']
        return Dish.objects.create(
            restaurant=restaurant,
            title=title,
            slug=_slug_unique(Dish, title),
            description=self.cleaned_data.get('description', ''),
            base_price=self.cleaned_data['base_price'],
            base_time_minutes=self.cleaned_data['base_time_minutes'],
            image=self.cleaned_data.get('image', ''),
            active=self.cleaned_data.get('active', True),
        )


class ProduitMarcheForm(forms.Form):
    """Produit de marché (marche.Produit) pour un vendeur MARCHÉ."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from marche.models import Categorie, Marche
            self.fields['categorie'].queryset = Categorie.objects.all()
            self.fields['marche'].queryset    = Marche.objects.all()
        except Exception:
            pass

    nom         = forms.CharField(label="Nom du produit", widget=forms.TextInput(attrs={'class': _INPUT}))
    categorie   = forms.ModelChoiceField(
        label="Catégorie", required=False, queryset=None,
        empty_label="— Sans catégorie —",
        widget=forms.Select(attrs={'class': _SELECT}),
    )
    marche      = forms.ModelChoiceField(
        label="Marché", required=False, queryset=None,
        empty_label="— Marché non précisé —",
        widget=forms.Select(attrs={'class': _SELECT}),
    )
    description = forms.CharField(label="Description", required=False, widget=forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}))
    prix        = forms.DecimalField(label="Prix (FCFA)", min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    prix_promo  = forms.DecimalField(label="Prix promotionnel", required=False, min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    promo_debut = forms.DateField(label="Début promotion", required=False, widget=forms.DateInput(attrs={'class': _INPUT, 'type': 'date'}))
    promo_fin   = forms.DateField(label="Fin promotion",   required=False, widget=forms.DateInput(attrs={'class': _INPUT, 'type': 'date'}))
    unite       = forms.CharField(label="Unité", initial="pièce", widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'pièce, kg, litre…'}))
    stock       = forms.IntegerField(label="Stock", initial=0, min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    disponibilite = forms.BooleanField(label="Disponible à la vente", required=False, initial=True)
    image       = forms.ImageField(label="Image principale", required=False, widget=forms.ClearableFileInput(attrs={'class': _INPUT}))

    def save_for_vendeur(self, vendeur_boutique):
        from marche.models import Produit
        return Produit.objects.create(
            vendeur=vendeur_boutique,
            nom=self.cleaned_data['nom'],
            categorie=self.cleaned_data.get('categorie'),
            marche=self.cleaned_data.get('marche'),
            description=self.cleaned_data.get('description', ''),
            prix=self.cleaned_data['prix'],
            prix_promo=self.cleaned_data.get('prix_promo'),
            promo_debut=self.cleaned_data.get('promo_debut'),
            promo_fin=self.cleaned_data.get('promo_fin'),
            unite=self.cleaned_data.get('unite', 'pièce') or 'pièce',
            stock=self.cleaned_data.get('stock', 0),
            disponibilite=self.cleaned_data.get('disponibilite', True),
            image=self.cleaned_data.get('image'),
        )


class ProduitShoppingForm(forms.Form):
    """Produit de boutique (shopping.Product) pour un vendeur SHOPPING."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from shopping.models import Category
            self.fields['category'].queryset = Category.objects.all()
        except Exception:
            pass

    name        = forms.CharField(label="Nom du produit", widget=forms.TextInput(attrs={'class': _INPUT}))
    category    = forms.ModelChoiceField(
        label="Catégorie", required=False, queryset=None,
        empty_label="— Sans catégorie —",
        widget=forms.Select(attrs={'class': _SELECT}),
    )
    description = forms.CharField(label="Description", widget=forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}))
    price       = forms.DecimalField(label="Prix (FCFA)", min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    prix_promo  = forms.DecimalField(label="Prix promotionnel", required=False, min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    promo_debut = forms.DateField(label="Début promotion", required=False, widget=forms.DateInput(attrs={'class': _INPUT, 'type': 'date'}))
    promo_fin   = forms.DateField(label="Fin promotion",   required=False, widget=forms.DateInput(attrs={'class': _INPUT, 'type': 'date'}))
    stock       = forms.IntegerField(label="Stock", initial=0, min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    active      = forms.BooleanField(label="Actif (visible sur le site)", required=False, initial=True)

    def save_for_shop(self, shop):
        from shopping.models import Product
        name = self.cleaned_data['name']
        return Product.objects.create(
            shop=shop,
            name=name,
            slug=_slug_unique(Product, name),
            category=self.cleaned_data.get('category'),
            description=self.cleaned_data['description'],
            price=self.cleaned_data['price'],
            prix_promo=self.cleaned_data.get('prix_promo'),
            promo_debut=self.cleaned_data.get('promo_debut'),
            promo_fin=self.cleaned_data.get('promo_fin'),
            stock=self.cleaned_data['stock'],
            active=self.cleaned_data.get('active', True),
        )


class ProduitPerruqueForm(forms.Form):
    """Perruque / extension (perruque.WigProduct) pour un vendeur PERRUQUE."""
    MATERIALS = [('natural','Naturelle'),('synthetic','Synthétique')]
    TEXTURES  = [('straight','Lisse'),('curly','Frisée'),('wavy','Ondulée'),
                 ('kinky','Kinky'),('body_wave','Body Wave'),('deep_wave','Deep Wave')]
    STATUSES  = [('available','Disponible'),('out_of_stock','Rupture de stock'),('preorder','Précommande')]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from perruque.models import Category
            self.fields['category'].queryset = Category.objects.all()
        except Exception:
            pass

    name        = forms.CharField(label="Nom du produit", widget=forms.TextInput(attrs={'class': _INPUT}))
    category    = forms.ModelChoiceField(
        label="Catégorie", required=False, queryset=None,
        empty_label="— Sans catégorie —",
        widget=forms.Select(attrs={'class': _SELECT}),
    )
    description = forms.CharField(label="Description", required=False, widget=forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}))
    price       = forms.DecimalField(label="Prix (FCFA)", min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    promotional_price = forms.DecimalField(label="Prix promotionnel", required=False, min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    promo_debut = forms.DateField(label="Début promotion", required=False, widget=forms.DateInput(attrs={'class': _INPUT, 'type': 'date'}))
    promo_fin   = forms.DateField(label="Fin promotion",   required=False, widget=forms.DateInput(attrs={'class': _INPUT, 'type': 'date'}))
    material    = forms.ChoiceField(label="Matière", choices=MATERIALS, widget=forms.Select(attrs={'class': _SELECT}))
    texture     = forms.ChoiceField(label="Texture", choices=TEXTURES,  widget=forms.Select(attrs={'class': _SELECT}))
    color       = forms.CharField(label="Couleur", widget=forms.TextInput(attrs={'class': _INPUT}))
    length      = forms.CharField(label='Longueur (ex : 12", 14")', widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': '12"'}))
    stock       = forms.IntegerField(label="Quantité en stock", initial=0, min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    status      = forms.ChoiceField(label="Statut", choices=STATUSES, widget=forms.Select(attrs={'class': _SELECT}))
    city        = forms.CharField(label="Ville", widget=forms.TextInput(attrs={'class': _INPUT}))
    location    = forms.CharField(label="Localisation / Quartier", widget=forms.TextInput(attrs={'class': _INPUT}))
    delivery_available = forms.BooleanField(label="Livraison disponible", required=False, initial=True)

    def save_for_shop(self, shop):
        from perruque.models import WigProduct
        return WigProduct.objects.create(
            shop=shop,
            name=self.cleaned_data['name'],
            category=self.cleaned_data.get('category'),
            description=self.cleaned_data.get('description', ''),
            price=self.cleaned_data['price'],
            promotional_price=self.cleaned_data.get('promotional_price'),
            promo_debut=self.cleaned_data.get('promo_debut'),
            promo_fin=self.cleaned_data.get('promo_fin'),
            material=self.cleaned_data['material'],
            texture=self.cleaned_data['texture'],
            color=self.cleaned_data.get('color', ''),
            length=self.cleaned_data.get('length', ''),
            stock=self.cleaned_data.get('stock', 0),
            status=self.cleaned_data.get('status', 'available'),
            city=self.cleaned_data.get('city', ''),
            location=self.cleaned_data.get('location', ''),
            delivery_available=self.cleaned_data.get('delivery_available', True),
        )


class ProduitVoitureForm(forms.Form):
    """Véhicule (voiture.Car) pour un vendeur VOITURE."""
    TRANSMISSIONS = [('manual','Manuelle'),('automatic','Automatique')]
    FUELS         = [('gasoline','Essence'),('diesel','Diesel'),('hybrid','Hybride'),('electric','Électrique')]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from voiture.models import CarCategory
            self.fields['category'].queryset = CarCategory.objects.all()
        except Exception:
            pass

    brand             = forms.CharField(label="Marque", widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Toyota, Renault…'}))
    model             = forms.CharField(label="Modèle", widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Corolla, Clio…'}))
    year              = forms.IntegerField(label="Année", min_value=1990, widget=forms.NumberInput(attrs={'class': _INPUT}))
    color             = forms.CharField(label="Couleur", required=False, widget=forms.TextInput(attrs={'class': _INPUT}))
    category          = forms.ModelChoiceField(
        label="Catégorie", required=False, queryset=None,
        empty_label="— Sans catégorie —", widget=forms.Select(attrs={'class': _SELECT}),
    )
    daily_price       = forms.DecimalField(label="Prix / jour (FCFA)", min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    promotional_price = forms.DecimalField(label="Prix promo / jour", required=False, min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    promo_debut       = forms.DateField(label="Début promotion", required=False, widget=forms.DateInput(attrs={'class': _INPUT, 'type': 'date'}))
    promo_fin         = forms.DateField(label="Fin promotion",   required=False, widget=forms.DateInput(attrs={'class': _INPUT, 'type': 'date'}))
    deposit           = forms.DecimalField(label="Caution (FCFA)", min_value=0, initial=0, required=False, widget=forms.NumberInput(attrs={'class': _INPUT}))
    seats             = forms.IntegerField(label="Nombre de places", min_value=1, initial=5, widget=forms.NumberInput(attrs={'class': _INPUT}))
    doors             = forms.IntegerField(label="Nombre de portes", min_value=1, initial=4, required=False, widget=forms.NumberInput(attrs={'class': _INPUT}))
    transmission      = forms.ChoiceField(label="Transmission", choices=TRANSMISSIONS, widget=forms.Select(attrs={'class': _SELECT}))
    fuel              = forms.ChoiceField(label="Carburant", choices=FUELS, widget=forms.Select(attrs={'class': _SELECT}))
    air_conditioning  = forms.BooleanField(label="Climatisation", required=False, initial=True)
    driver_included   = forms.BooleanField(label="Chauffeur inclus", required=False)
    city              = forms.CharField(label="Ville", required=False, widget=forms.TextInput(attrs={'class': _INPUT}))
    location          = forms.CharField(label="Lieu de prise en charge", required=False, widget=forms.TextInput(attrs={'class': _INPUT}))
    description       = forms.CharField(label="Description", required=False, widget=forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}))

    def save_for_shop(self, shop):
        from voiture.models import Car
        return Car.objects.create(
            shop=shop,
            brand=self.cleaned_data['brand'],
            model=self.cleaned_data['model'],
            year=self.cleaned_data['year'],
            color=self.cleaned_data.get('color', ''),
            category=self.cleaned_data.get('category'),
            daily_price=self.cleaned_data['daily_price'],
            promotional_price=self.cleaned_data.get('promotional_price'),
            promo_debut=self.cleaned_data.get('promo_debut'),
            promo_fin=self.cleaned_data.get('promo_fin'),
            deposit=self.cleaned_data.get('deposit') or 0,
            seats=self.cleaned_data.get('seats', 5),
            doors=self.cleaned_data.get('doors', 4) or 4,
            transmission=self.cleaned_data['transmission'],
            fuel=self.cleaned_data['fuel'],
            air_conditioning=self.cleaned_data.get('air_conditioning', True),
            driver_included=self.cleaned_data.get('driver_included', False),
            city=self.cleaned_data.get('city', ''),
            location=self.cleaned_data.get('location', ''),
            description=self.cleaned_data.get('description', ''),
            status='available',
        )


class ProduitImmobilierForm(forms.Form):
    """Bien immobilier (immobilier.Immobilier) pour un vendeur IMMOBILIER."""
    TYPES_BIEN  = [('maison','Maison'),('appartement','Appartement'),('studio','Studio'),
                   ('villa','Villa'),('terrain','Terrain'),('bureau','Bureau'),
                   ('commerce','Local commercial'),('entrepot','Entrepôt')]
    TYPES_OFFRE = [('vente','Vente'),('location','Location')]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from immobilier.models import ImmobilierCategory
            self.fields['categorie'].queryset = ImmobilierCategory.objects.all()
        except Exception:
            pass

    titre         = forms.CharField(label="Titre de l'annonce", widget=forms.TextInput(attrs={'class': _INPUT}))
    type_bien     = forms.ChoiceField(label="Type de bien", choices=TYPES_BIEN, widget=forms.Select(attrs={'class': _SELECT}))
    type_offre    = forms.ChoiceField(label="Type d'offre", choices=TYPES_OFFRE, widget=forms.Select(attrs={'class': _SELECT}))
    categorie     = forms.ModelChoiceField(
        label="Catégorie", required=False, queryset=None,
        empty_label="— Sans catégorie —", widget=forms.Select(attrs={'class': _SELECT}),
    )
    prix          = forms.DecimalField(label="Prix (FCFA)", min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    prix_promo    = forms.DecimalField(label="Prix promotionnel", required=False, min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    superficie    = forms.DecimalField(label="Superficie (m²)", required=False, min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    nombre_chambres    = forms.IntegerField(label="Chambres", required=False, min_value=0, initial=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    nombre_salles_bain = forms.IntegerField(label="Salles de bain", required=False, min_value=0, initial=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    nombre_salons      = forms.IntegerField(label="Salons", required=False, min_value=0, initial=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    nombre_cuisines    = forms.IntegerField(label="Cuisines", required=False, min_value=0, initial=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    nombre_garages     = forms.IntegerField(label="Garages", required=False, min_value=0, initial=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    description   = forms.CharField(label="Description", required=False, widget=forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 4}))
    adresse       = forms.CharField(label="Adresse / Quartier", required=False, widget=forms.TextInput(attrs={'class': _INPUT}))
    meuble        = forms.BooleanField(label="Meublé", required=False)
    piscine       = forms.BooleanField(label="Piscine", required=False)
    parking       = forms.BooleanField(label="Parking", required=False)
    climatisation = forms.BooleanField(label="Climatisation", required=False)
    gardiennage   = forms.BooleanField(label="Gardiennage", required=False)

    def save_for_shop(self, shop):
        from immobilier.models import Immobilier
        return Immobilier.objects.create(
            vendeur=shop,                    # FK s'appelle 'vendeur' → Boutique
            titre=self.cleaned_data['titre'],
            type_bien=self.cleaned_data['type_bien'],
            type_offre=self.cleaned_data['type_offre'],
            categorie=self.cleaned_data.get('categorie'),
            prix=self.cleaned_data['prix'],
            prix_promotionnel=self.cleaned_data.get('prix_promo'),
            superficie=self.cleaned_data.get('superficie'),
            nombre_chambres=self.cleaned_data.get('nombre_chambres', 0) or 0,
            nombre_salles_bain=self.cleaned_data.get('nombre_salles_bain', 0) or 0,
            nombre_salons=self.cleaned_data.get('nombre_salons', 0) or 0,
            nombre_cuisines=self.cleaned_data.get('nombre_cuisines', 0) or 0,
            nombre_garages=self.cleaned_data.get('nombre_garages', 0) or 0,
            description=self.cleaned_data.get('description', ''),
            adresse=self.cleaned_data.get('adresse', ''),
            meuble=self.cleaned_data.get('meuble', False),
            piscine=self.cleaned_data.get('piscine', False),
            parking=self.cleaned_data.get('parking', False),
            climatisation=self.cleaned_data.get('climatisation', False),
            gardiennage=self.cleaned_data.get('gardiennage', False),
            statut='disponible',
        )


class ProduitQuicaillerieForm(forms.Form):
    """Produit de quincaillerie (quicaillerie.ProduitQuincaillerie) pour un vendeur QUINCAILLERIE."""
    ETATS   = [('neuf','Neuf'),('occasion','Occasion')]
    STATUTS = [('disponible','Disponible'),('rupture','Rupture de stock'),('precommande','Précommande')]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from quicaillerie.models import CategorieQuincaillerie
            self.fields['categorie'].queryset = CategorieQuincaillerie.objects.all()
        except Exception:
            pass

    nom               = forms.CharField(label="Nom du produit", widget=forms.TextInput(attrs={'class': _INPUT}))
    categorie         = forms.ModelChoiceField(
        label="Catégorie", required=False, queryset=None,
        empty_label="— Sans catégorie —", widget=forms.Select(attrs={'class': _SELECT}),
    )
    reference         = forms.CharField(label="Référence", required=False, widget=forms.TextInput(attrs={'class': _INPUT}))
    marque            = forms.CharField(label="Marque", required=False, widget=forms.TextInput(attrs={'class': _INPUT}))
    description       = forms.CharField(label="Description", required=False, widget=forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}))
    prix              = forms.DecimalField(label="Prix (FCFA)", min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    prix_promotionnel = forms.DecimalField(label="Prix promotionnel", required=False, min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    quantite_stock    = forms.IntegerField(label="Quantité en stock", initial=0, min_value=0, widget=forms.NumberInput(attrs={'class': _INPUT}))
    unite             = forms.CharField(label="Unité", initial="Pièce", required=False, widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Pièce, Kg, m²…'}))
    etat              = forms.ChoiceField(label="État", choices=ETATS, widget=forms.Select(attrs={'class': _SELECT}))
    statut            = forms.ChoiceField(label="Statut", choices=STATUTS, widget=forms.Select(attrs={'class': _SELECT}))
    garantie          = forms.CharField(label="Garantie", required=False, widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ex: 1 an'}))
    ville             = forms.CharField(label="Ville", widget=forms.TextInput(attrs={'class': _INPUT}))
    adresse           = forms.CharField(label="Adresse / Quartier", widget=forms.TextInput(attrs={'class': _INPUT}))
    livraison_disponible = forms.BooleanField(label="Livraison disponible", required=False, initial=True)

    def save_for_shop(self, shop):
        from quicaillerie.models import ProduitQuincaillerie
        return ProduitQuincaillerie.objects.create(
            boutique=shop,                   # FK s'appelle 'boutique' → Boutique
            nom=self.cleaned_data['nom'],
            categorie=self.cleaned_data.get('categorie'),
            reference=self.cleaned_data.get('reference', ''),
            marque=self.cleaned_data.get('marque', ''),
            description=self.cleaned_data.get('description', ''),
            prix=self.cleaned_data['prix'],
            prix_promotionnel=self.cleaned_data.get('prix_promotionnel'),
            quantite_stock=self.cleaned_data.get('quantite_stock', 0),
            unite=self.cleaned_data.get('unite', 'Pièce') or 'Pièce',
            etat=self.cleaned_data.get('etat', 'neuf'),
            statut=self.cleaned_data.get('statut', 'disponible'),
            garantie=self.cleaned_data.get('garantie', ''),
            ville=self.cleaned_data.get('ville', ''),
            adresse=self.cleaned_data.get('adresse', ''),
            livraison_disponible=self.cleaned_data.get('livraison_disponible', True),
        )


# ══════════════════════════════════════════════════════════════════════════════
# Boutique / Shop form
# ══════════════════════════════════════════════════════════════════════════════
class BoutiqueForm(forms.Form):
    """Création d'une boutique (shopping.Shop) pour un vendeur."""
    name        = forms.CharField(label="Nom de la boutique", widget=forms.TextInput(attrs={'class': _INPUT}))
    description = forms.CharField(label="Description", widget=forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}))
    address     = forms.CharField(label="Adresse", required=False, widget=forms.TextInput(attrs={'class': _INPUT}))
    logo        = forms.ImageField(label="Logo", required=False, widget=forms.ClearableFileInput(attrs={'class': _INPUT}))

    def save_for_vendor(self, vendor):
        from shopping.models import Shop
        from django.utils.text import slugify
        import uuid
        name = self.cleaned_data['name']
        slug = slugify(name)
        if Shop.objects.filter(slug=slug).exists():
            slug = f'{slug}-{uuid.uuid4().hex[:6]}'
        return Shop.objects.create(
            vendor=vendor,
            name=name, slug=slug,
            description=self.cleaned_data['description'],
            address=self.cleaned_data.get('address', ''),
            logo=self.cleaned_data.get('logo'),
            active=True,
        )