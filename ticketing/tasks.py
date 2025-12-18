from celery import shared_task
from django.utils import timezone
from .models.tickets import Ticket, TicketStatus, TicketHistory
from .utils.notifications_utils import notify_auto_status_update

@shared_task
def escalate_expired_tickets():
    now = timezone.now()
    escalated_status = TicketStatus.objects.get(status="Escalated")

    tickets = Ticket.objects.filter(
        deadline__lt=now,
        status__status__in=["In-Progress", "Waiting-For-Customer"]
    )

    for ticket in tickets:
        old_status = ticket.status.status
        ticket.status = escalated_status
        ticket.save(update_fields=["status"])

        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=ticket.creator_id,
            old_status=old_status,
            new_status=escalated_status.status
        )

        notify_auto_status_update(
            ticket=ticket,
            old_status=old_status,
            new_status=escalated_status.status,
            notifier=ticket.creator_id
        )


@shared_task
def auto_close_inactive_tickets():
    limit = timezone.now() - timezone.timedelta(days=1)
    closed = TicketStatus.objects.get(status="Closed")

    tickets = Ticket.objects.filter(
        status__status="Waiting-For-Customer",
        changed_at__lt=limit
    )

    for ticket in tickets:
        old_status = ticket.status.status
        ticket.status = closed
        ticket.save(update_fields=["status"])

        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=ticket.creator_id,
            old_status=old_status,
            new_status=closed.status
        )

        notify_auto_status_update(
            ticket=ticket,
            old_status=old_status,
            new_status=closed.status,
            notifier=ticket.creator_id
        )
