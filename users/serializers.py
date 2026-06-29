from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class PhoneTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["phone"] = user.username
        return token

    def validate(self, attrs):
        # Accepte "username" ou "telephone" comme identifiant
        identifier = attrs.get("username", "").strip()
        password = attrs.get("password", "")

        user = None

        # 1. Essai direct par username
        user = authenticate(
            request=self.context.get("request"),
            username=identifier,
            password=password,
        )

        # 2. Si raté, cherche par champ telephone et réessaie
        if user is None:
            try:
                db_user = User.objects.get(telephone=identifier)
                user = authenticate(
                    request=self.context.get("request"),
                    username=db_user.username,
                    password=password,
                )
            except User.DoesNotExist:
                pass

        if user is None or not user.is_active:
            raise serializers.ValidationError(
                {"detail": "Numéro de téléphone ou mot de passe incorrect."}
            )

        refresh = self.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "role": user.role,
            "telephone": user.telephone or user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_id": user.id,
        }
