from django.contrib.auth.hashers import make_password,check_password
from rest_framework import serializers
from ..models.users import AppUser,Account,UserType
from rest_framework_simplejwt.tokens import RefreshToken


class CustomerSignupSerializer(serializers.Serializer):
    portal=serializers.CharField(max_length=255)
    name=serializers.CharField(max_length=255)
    email=serializers.EmailField()
    password=serializers.CharField(write_only=True)

    def validate_portal(self,value):
        if Account.objects.filter(portal=value).exists():
            raise serializers.ValidationError("Portal already exists")
        return value

    def create(self,validated_data):
        account=Account.objects.create(portal=validated_data["portal"])

        user=AppUser.objects.create(
            account_id=account,
            name=validated_data["name"],
            email=validated_data["email"],
            password=make_password(validated_data["password"]),
            role=UserType.CUSTOMER,
        )
        return user


class AgentCreateSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True)

    class Meta:
        model=AppUser
        fields=("name", "email", "password", "job_title")

    def create(self, validated_data):
        customer = self.context["request"].user

        agent = AppUser.objects.create(
            account_id=customer.account_id,
            name=validated_data["name"],
            email=validated_data["email"],
            password=make_password(validated_data["password"]),
            job_title=validated_data["job_title"],
            role=UserType.AGENT,
        )
        return agent

class LoginSerializer(serializers.Serializer):
    portal = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        portal=attrs.get("portal")
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            account = Account.objects.get(portal=portal)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Portal does not exists")

        try:
            user = AppUser.objects.get(email=email, account_id=account)
        except AppUser.DoesNotExist:
            raise serializers.ValidationError("this user does not exists.")

        if not check_password(password, user.password):
            raise serializers.ValidationError("Incorrect password")

        refresh=RefreshToken.for_user(user)

        return {
            "refresh":str(refresh),
            "access_token":str(refresh.access_token),
            "user_id": user.id,
            "name": user.name,
            "portal": account.portal,
        }
