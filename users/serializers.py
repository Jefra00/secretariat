from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class PhoneTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 🔥 AJOUT INFOS USER DANS TOKEN
        token["role"] = user.role
        token["phone"] = user.username

        return token