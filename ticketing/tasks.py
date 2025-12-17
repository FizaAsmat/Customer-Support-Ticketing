from celery import shared_task
from django.utils import timezone
from .models.tickets import Ticket, TicketStatus

@shared_task
def escalate_expired_tickets():
    now = timezone.now()

    escalated_status = TicketStatus.objects.get(status="Escalated")

    tickets = Ticket.objects.filter(
        deadline__lt=now,
        status__status__in=["In-Progress", "Waiting-For-Customer"]
    )

    for ticket in tickets:
        ticket.status = escalated_status
        ticket.save(update_fields=["status"])

@shared_task
def auto_close_inactive_tickets():
    limit = timezone.now() - timezone.timedelta(days=1)
    closed = TicketStatus.objects.get(status="Closed")

    tickets = Ticket.objects.filter(
        status__status="Waiting-For-Customer",
        changed_at__lt=limit
    )

    for ticket in tickets:
        ticket.status = closed
        ticket.save(update_fields=["status"])
