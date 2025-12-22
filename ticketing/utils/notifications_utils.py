from django.db import transaction
from ..models.notifications import Notification, NotificationRecipient, TicketPurpose
from ..models.tickets import Ticket
from ..models.comments import Thread, Comment
from ..models.users import AppUser


def _create_notification(ticket, notifier, purpose, recipients):
    if not recipients:
        return

    with transaction.atomic():
        notification = Notification.objects.create(
            ticket=ticket,
            notifier=notifier,
            purpose=purpose
        )

        recipient_objs = [
            NotificationRecipient(notification=notification, user=user)
            for user in set(recipients)
        ]

        NotificationRecipient.objects.bulk_create(recipient_objs)

def notify_ticket_created(ticket: Ticket, created_by):
    if ticket.assignee_id:
        recipients = [
            ticket.creator_id,
            ticket.assignee_id
        ]
    else:
        agents = AppUser.objects.filter(
            role="AGENT",
            account_id=ticket.creator_id.account_id
        )
        recipients = list(agents) + [ticket.creator_id]

    _create_notification(
        ticket=ticket,
        notifier=created_by,
        purpose=TicketPurpose.Ticket_Created,
        recipients=recipients
    )

def notify_ticket_assigned(ticket: Ticket, assigned_by):
    if not ticket.assignee_id:
        return

    recipients = [
        ticket.assignee_id,
        ticket.creator_id
    ]

    _create_notification(
        ticket=ticket,
        notifier=assigned_by,
        purpose=TicketPurpose.Ticked_Assigned,
        recipients=recipients
    )

def notify_ticket_status_updated(ticket: Ticket, updated_by, old_status):

    recipients = [ticket.creator_id]
    if ticket.assignee_id:
        recipients.append(ticket.assignee_id)

    purpose = f"{updated_by.name} changed status of Ticket: '{ticket.title}' from '{old_status.status}' to '{ticket.status.status}'"

    _create_notification(
        ticket=ticket,
        notifier=updated_by,
        purpose=purpose,
        recipients=recipients
    )

def notify_comment_added(comment: Comment, commented_by):
    ticket = comment.ticket

    if ticket.assignee_id:
        recipients = [
            ticket.creator_id,
            ticket.assignee_id
        ]

    else:
        agents = AppUser.objects.filter(
            role="AGENT",
            account_id=ticket.creator_id.account_id
        )
        recipients = list(agents) + [ticket.creator_id]

    purpose = (
        f"{commented_by.name} has commented on Ticket "
        f"'{ticket.title}':\n{comment.thread.body}"
    )

    _create_notification(
        ticket=ticket,
        notifier=commented_by,
        purpose=purpose,
        recipients=recipients
    )


def notify_reply_added(thread: Thread, replied_by):
    try:
        comment = Comment.objects.get(thread__thread_group=thread.thread_group)
    except Comment.DoesNotExist:
        return

    ticket = comment.ticket

    participant_ids = Thread.objects.filter(thread_group=thread.thread_group).values_list("commented_by_id", flat=True)
    recipients = AppUser.objects.filter(id__in=participant_ids)

    purpose = f"{replied_by.name} replied on Ticket '{ticket.title}': \n {thread.body}"

    _create_notification(
        ticket=ticket,
        notifier=replied_by,
        purpose=purpose,
        recipients=recipients
    )

def notify_auto_status_update(
    ticket,
    old_status,
    new_status,
    notifier
):
    recipients = []

    if ticket.creator_id:
        recipients.append(ticket.creator_id)

    if ticket.assignee_id:
        recipients.append(ticket.assignee_id)

    purpose = (
        f"{notifier.name} has changed the ticket status "
        f"from '{old_status}' to '{new_status}'"
    )

    _create_notification(
        ticket=ticket,
        notifier=notifier,
        purpose=purpose,
        recipients=recipients
    )