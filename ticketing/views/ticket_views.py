from django.shortcuts import render, redirect
from django.views import View
from django.utils import timezone
from ..models.tickets import Ticket
from ..serializers.ticket_form import TicketForm
from ..permissions import CustomerRequiredMixin

class CustomerTicketCreateView(CustomerRequiredMixin, View):
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

            ticket.save()
            return redirect("customer_dashboard_page")

        return render(request, "ticket_form.html", {"form": form})
