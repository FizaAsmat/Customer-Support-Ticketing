from django.views import View
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

            if ticket.assignee_id:
                ticket.start_time = timezone.now()
                ticket.deadline = ticket.start_time + ticket.priority_id.duration
                ticket.status = TicketStatus.objects.get(status="In-Progress")

            ticket.save(updated_by=request.user)
            return redirect("customer_dashboard_page")

        return render(request, "ticket_form.html", {"form": form})
