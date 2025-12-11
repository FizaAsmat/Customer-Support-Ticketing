from django.shortcuts import render, redirect
from django.views import View
from ..serializers.user_form import CustomerSignupForm, AgentCreateForm, LoginForm
from ..models.users import UserType, AppUser
from ..permissions import CustomerRequiredMixin, AgentRequiredMixin


class CustomerSignupView(View):
    def get(self, request):
        form = CustomerSignupForm()
        return render(request, "signup.html", {"form": form})

    def post(self, request):
        form = CustomerSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Store both user_id and account_id in session for multi-tenant checks
            request.session['user_id'] = user.id
            request.session['account_id'] = user.account_id.id
            request.session['role'] = user.role
            return redirect("customer_dashboard_page")
        return render(request, "signup.html", {"form": form})


class LoginView(View):

    def get(self, request):
        if request.session.get("user_id") and request.session.get("account_id"):
            role = request.session.get("role")
            if role == UserType.CUSTOMER:
                return redirect("customer_dashboard_page")
            else:
                return redirect("agent_dashboard_page")

        form = LoginForm()
        return render(request, "login.html", {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.user
            # Manual session login (multi-tenant safe)
            request.session['user_id'] = user.id
            request.session['account_id'] = user.account_id.id
            request.session['role'] = user.role
            # Redirect based on role
            if user.role == UserType.CUSTOMER:
                return redirect("customer_dashboard_page")
            else:
                return redirect("agent_dashboard_page")
        return render(request, "login.html", {"form": form})


class LogoutView(View):
    def get(self, request):
        request.session.flush()  # Clear all session data
        return redirect("/login/")


class AgentCreateView(CustomerRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        form = AgentCreateForm()
        return render(request, "agent_form.html", {"form": form})

    def post(self, request):
        form = AgentCreateForm(request.POST)
        if form.is_valid():
            form.save(customer=request.user)
            return redirect("customer_dashboard_page")
        return render(request, "customer_dashboard.html",{
            "user": request.user,
            "agents_form": form
        })


class CustomerDashboardPageView(CustomerRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        user = request.user

        agents = AppUser.objects.filter(account_id=user.account_id, role=UserType.AGENT)
        return render(request, "dashboard.html", {
            "user": user,
            "agents": agents
        })


class AgentDashboardPageView(AgentRequiredMixin, View):
    login_url = "/login/"


    def get(self, request):

        return render(request, "dashboard.html", {"user": request.user})
