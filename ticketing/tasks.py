from celery import shared_task
from django.utils import timezone
from .models.tickets import Ticket, TicketStatus, TicketHistory
from .models.users import AppUser
from .utils.notifications_utils import _create_notification  # use internal function

@shared_task
def escalate_expired_tickets():
    now = timezone.now()
    escalated_status = TicketStatus.objects.get(status="Escalated")
    system_user = AppUser.objects.get(email="system@internal")

    tickets = Ticket.objects.filter(
        deadline__lt=now,
        status__status__in=["In-Progress", "Waiting-For-Customer"]
    )

    for ticket in tickets:
        old_status = ticket.status.status
        ticket.status = escalated_status
        ticket.save(updated_by=system_user)

        # Create notification
        recipients = [ticket.creator_id]
        if ticket.assignee_id:
            recipients.append(ticket.assignee_id)

        _create_notification(
            ticket=ticket,
            notifier=system_user,
            purpose=f"Ticket '{ticket.title}' auto escalated from '{old_status}' to 'Escalated'",
            recipients=recipients
        )


@shared_task
def auto_close_inactive_tickets():
    limit = timezone.now() - timezone.timedelta(days=1)
    closed_status = TicketStatus.objects.get(status="Closed")
    system_user = AppUser.objects.get(email="system@internal")

    tickets = Ticket.objects.filter(
        status__status="Waiting-For-Customer",
        changed_at__lt=limit
    )

    for ticket in tickets:
        old_status = ticket.status.status
        ticket.status = closed_status
        ticket.save(updated_by=system_user)

        recipients = [ticket.creator_id]
        if ticket.assignee_id:
            recipients.append(ticket.assignee_id)

        _create_notification(
            ticket=ticket,
            notifier=system_user,
            purpose=f"Ticket '{ticket.title}' auto closed due to inactivity",
            recipients=recipients
        )
