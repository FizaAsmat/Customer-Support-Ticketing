from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.views import View
from ..serializers.user_form import CustomerSignupForm, AgentCreateForm, LoginForm
from ..models.users import UserType, AppUser
from ..permissions import CustomerRequiredMixin, AgentRequiredMixin, AccountAwareMixin
from ..models.tickets import Ticket, TicketStatus

class CustomerSignupView(View):
    def get(self, request):
        form = CustomerSignupForm()
        return render(request, "signup.html", {"form": form})

    def post(self, request):
        form = CustomerSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
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
            request.session['user_id'] = user.id
            request.session['account_id'] = user.account_id.id
            request.session['role'] = user.role
            if user.role == UserType.CUSTOMER:
                return redirect("customer_dashboard_page")
            else:
                return redirect("agent_dashboard_page")
        return render(request, "login.html", {"form": form})


class LogoutView(View):
    def get(self, request):
        request.session.flush()
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

class CustomerDashboardPageView(CustomerRequiredMixin, AccountAwareMixin, View):
    login_url = "/login/"

    def get(self, request):
        user = request.user

        agents = AppUser.objects.filter(
            account_id=user.account_id,
            role=UserType.AGENT,
            is_active=True
        )

        tickets = Ticket.objects.filter(
            creator_id=user.id
        ).select_related(
            "status", "priority_id", "assignee_id"
        )

        statuses = TicketStatus.objects.all().order_by("id")

        status_columns = []
        for status in statuses:
            status_columns.append({
                "status": status,
                "tickets": tickets.filter(status=status)
            })

        return render(request, "dashboard.html", {
            "user": user,
            "agents": agents,
            "tickets": tickets,
            "status_columns": status_columns,
        })

class AgentDashboardPageView(AgentRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        user = request.user

        assigned_tickets = Ticket.objects.filter(
            assignee_id=user.id
        ).select_related(
            "status", "priority_id", "assignee_id"
        )

        todo_status = TicketStatus.objects.get(status="TODO")
        unassigned_todo_tickets = Ticket.objects.filter(
            status=todo_status,
            assignee_id__isnull=True,
            creator_id__account_id=user.account_id
        ).select_related("status", "priority_id", "creator_id")

        statuses = TicketStatus.objects.all().order_by("id")
        status_columns = []
        for status in statuses:
            status_columns.append({
                "status": status,
                "tickets": assigned_tickets.filter(status=status)
            })

        return render(request, "dashboard.html", {
            "user": user,
            "status_columns": status_columns,
            "unassigned_todo_tickets": unassigned_todo_tickets,
        })

class AgentSoftDeleteView(CustomerRequiredMixin, View):
    login_url = "/login/"

    def post(self, request, agent_id):
        agent = get_object_or_404(AppUser, id=agent_id, role=UserType.AGENT)

        agent.is_active = False
        agent.deleted_at = timezone.now()
        agent.save()

        affected_statuses = ["TODO", "In-Progress", "Waiting-For-Customer","Escalated"]
        todo_status = TicketStatus.objects.get(status="TODO")

        tickets_to_update = Ticket.objects.filter(
            assignee_id=agent,
            status__status__in=affected_statuses
        )

        for ticket in tickets_to_update:
            ticket.assignee_id = None
            ticket.status = todo_status
            ticket.start_time = None
            ticket.deadline = None
            ticket.save(updated_by=request.user)

        messages.success(request, f"Agent {agent.name} has been deleted and {tickets_to_update.count()} tickets updated.")
        return redirect("customer_dashboard_page")