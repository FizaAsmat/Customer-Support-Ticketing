from django import forms
from django.contrib.auth.hashers import make_password,check_password
from ..models.users import AppUser, Account, UserType
from django.core.exceptions import ValidationError


class CustomerSignupForm(forms.Form):
    portal = forms.CharField(max_length=255)
    name = forms.CharField(max_length=255)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_portal(self):
        portal = self.cleaned_data.get("portal")
        if Account.objects.filter(portal=portal).exists():
            raise forms.ValidationError("Portal already exists")
        return portal

    def save(self):
        # called after form.is_valid()
        portal = self.cleaned_data["portal"]
        name = self.cleaned_data["name"]
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password"]

        account = Account.objects.create(portal=portal)
        user = AppUser.objects.create(
            account_id=account,
            name=name,
            email=email,
            password=make_password(password),
            role=UserType.CUSTOMER,
        )
        return user


class AgentCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = AppUser
        fields = ("name", "email", "password", "job_title")

    def save(self, customer, commit=True):
        agent = super().save(commit=False)
        agent.account_id = customer.account_id
        agent.password = make_password(self.cleaned_data["password"])
        agent.role = UserType.AGENT
        if commit:
            agent.save()
        return agent


class LoginForm(forms.Form):
    portal = forms.CharField(max_length=255)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        portal = cleaned_data.get("portal")
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        try:
            account = Account.objects.get(portal=portal)
        except Account.DoesNotExist:
            raise forms.ValidationError("Portal does not exist")

        try:
            user = AppUser.objects.get(email=email, account_id=account)
        except AppUser.DoesNotExist:
            raise forms.ValidationError("User does not exist")

        if not check_password(password, user.password):
            raise forms.ValidationError("Incorrect password")

        if user.role == UserType.AGENT and not user.is_active:
            raise ValidationError("Your agent account has been deactivated. Contact admin.")

        # store user object for view to login
        self.user = user
        return cleaned_data

