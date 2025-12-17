from django.shortcuts import redirect
from django.views import View
from .models.users import UserType, AppUser

class CustomerRequiredMixin(View):
    login_url = "/login/"

    def dispatch(self, request, *args, **kwargs):
        user_id = request.session.get("user_id")
        account_id = request.session.get("account_id")
        if not user_id or not account_id:
            return redirect(self.login_url)
        try:
            user = AppUser.objects.get(id=user_id, account_id=account_id)
        except AppUser.DoesNotExist:
            return redirect(self.login_url)
        if user.role != UserType.CUSTOMER:
            return redirect(self.login_url)
        request.user = user
        return super().dispatch(request, *args, **kwargs)


class AgentRequiredMixin(View):
    login_url = "/login/"

    def dispatch(self, request, *args, **kwargs):
        user_id = request.session.get("user_id")
        account_id = request.session.get("account_id")
        if not user_id or not account_id:
            return redirect(self.login_url)
        try:
            user = AppUser.objects.get(id=user_id, account_id=account_id)
        except AppUser.DoesNotExist:
            return redirect(self.login_url)
        if user.role != UserType.AGENT:
            return redirect(self.login_url)
        request.user = user
        return super().dispatch(request, *args, **kwargs)


class AccountAwareMixin(View):
    login_url = "/login/"

    def dispatch(self, request, *args, **kwargs):
        user_id = request.session.get("user_id")

        if not user_id:
            return redirect(self.login_url)

        try:
            request.user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return redirect(self.login_url)

        return super().dispatch(request, *args, **kwargs)

    def filter_queryset_by_account(self, queryset, user_field="creator_id"):
        filter_kwargs = {f"{user_field}__account_id": self.request.user.account_id}
        return queryset.filter(**filter_kwargs)