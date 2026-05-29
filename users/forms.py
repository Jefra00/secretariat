from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib.auth.forms import UserChangeForm
from .models import User


class ClientLoginForm(forms.Form):
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Votre adresse e-mail',
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
            }
        )
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '••••••••',
                'class': 'w-full rounded-lg border-slate-300 dark:border-slate-700 '
                         'bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email.lower())
            except User.DoesNotExist:
                raise forms.ValidationError("Aucun compte n’est associé à cette adresse e-mail.")

            user = authenticate(username=user.username, password=password)
            if user is None:
                raise forms.ValidationError("Adresse e-mail ou mot de passe incorrect.")
            if not user.statut:
                raise forms.ValidationError("Ce compte est désactivé. Veuillez contacter le support.")

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

        # Optionnel : masquer le champ "role" si l'utilisateur n’est pas superadmin
        request = kwargs.get('request')
        if request and not request.user.is_superuser:
            self.fields['role'].widget = forms.HiddenInput()
            self.fields['role'].initial = 'employe'


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'telephone', 'adresse', 
            'pays', 'bio', 'avatar', 'langue', 'role'
        ]
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Si un utilisateur existant est passé, on masque les champs déjà remplis
        if user:
            for field_name in list(self.fields.keys()):
                # Si la valeur existe, on supprime le champ du formulaire
                if getattr(user, field_name, None):
                    self.fields.pop(field_name, None)

        # On adapte les labels / placeholders pour la cohérence
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