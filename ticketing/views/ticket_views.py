from django.views import View
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.utils import timezone
from ..serializers.ticket_form import TicketForm, TicketUpdateForm
from ..models.tickets import Ticket, TicketHistory, TicketStatus
from ..permissions import CustomerRequiredMixin, AgentRequiredMixin, AccountAwareMixin

class CustomerTicketCreateView(CustomerRequiredMixin, AccountAwareMixin, View):
    login_url = "/login/"

    def get(self, request):
        form = TicketForm(user=request.user)
        return render(request, "ticket_form.html", {"form": form})

    def post(self, request):
        form = TicketForm(request.POST, user=request.user)

        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.creator_id = request.user

            duration_map = {
                "1h": timedelta(hours=1),
                "4h": timedelta(hours=4),
                "8h": timedelta(hours=8),
                "1d": timedelta(days=1),
                "2d": timedelta(days=2),
            }

            selected_duration = form.cleaned_data.get("duration")
            sla_duration = duration_map.get(selected_duration)

            if not sla_duration and ticket.priority_id:
                sla_duration = ticket.priority_id.duration

            if ticket.assignee_id:
                ticket.start_time = timezone.now()
                ticket.deadline = ticket.start_time + sla_duration
                ticket.status = TicketStatus.objects.get(status="In-Progress")

            ticket.save(updated_by=request.user)
            return redirect("customer_dashboard_page")

        return render(request, "ticket_form.html", {"form": form})

class TicketUpdateView(CustomerRequiredMixin, View):
    login_url = "/login/"

    def get_ticket(self, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        if ticket.creator_id.account_id != self.request.user.account_id:
            return None
        return ticket

    def get(self, request, pk):
        ticket = self.get_ticket(pk)
        if not ticket:
            return HttpResponseForbidden("You cannot update this ticket.")
        form = TicketUpdateForm(instance=ticket, ticket=ticket, user=request.user)
        return render(request, "ticket_update.html", {"form": form, "ticket": ticket})

    def post(self, request, pk):
        ticket = self.get_ticket(pk)
        if not ticket:
            return HttpResponseForbidden("Only customers can update tickets.")

        form = TicketUpdateForm(
            request.POST,
            instance=ticket,
            ticket=ticket,
            user=request.user
        )

        if form.is_valid():
            updated_ticket = form.save(commit=False)
            updated_ticket.save(updated_by=request.user)
            return redirect("customer_dashboard_page")

        return render(request, "ticket_update.html", {"form": form, "ticket": ticket})

