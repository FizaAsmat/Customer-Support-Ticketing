from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from ..models.users import AppUser,Account,UserType
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True)

    class Meta:
        model=AppUser
        fields=("name","email","password","job")

class AccountSerializer(serializers.ModelSerializer):
    user=UserSerializer(many=True)

    class Meta:
        model=Account
        fields=("profile")

    def create(self,validate_data):
        user_data=validate_data.pop('user')
        account_data=Account.objects.create(**validate_data)

        for data in user_data:
            AppUser.objects.create(account_data=account_data,**data)

        return account_data

class BaseTokenSerializer(TokenObtainPairSerializer):
    required_role = None

    def validate(self, attrs):
        portal=attrs.get("portal")
        email = attrs.get("email")
        password = attrs.get("password")

        if self.required_role is None:
            raise AuthenticationFailed("Role not configured for this serializer")

        # Fetch only users of the required role
        try:
            user = AppUser.objects.get(email=email, role=self.required_role)
        except AppUser.DoesNotExist:
            raise AuthenticationFailed(f"{self.required_role} does not exist")

        if not check_password(password, user.password):
            raise AuthenticationFailed("Incorrect password")

        # Continue JWT creation
        data = super().validate(attrs)

        # Add user type to token response
        data["portal"]=Account.portal
        data["role"] = user.role
        data["user_id"] = user.id
        data["name"] = user.name

        return data


class CustomerLoginSerializer(BaseTokenSerializer):
    required_role = UserType.CUSTOMER


class AgentLoginSerializer(BaseTokenSerializer):
    required_role = UserType.AGENT