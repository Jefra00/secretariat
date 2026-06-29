from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class PhoneAuthBackend(ModelBackend):
    """
    Authentification par numéro de téléphone + mot de passe.
    Le numéro est normalisé (espaces et tirets supprimés) avant comparaison.
    """

    def authenticate(self, request, telephone=None, password=None, **kwargs):
        if not telephone or not password:
            return None

        phone = telephone.replace(' ', '').replace('-', '')
        try:
            user = User.objects.get(telephone=phone)
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
