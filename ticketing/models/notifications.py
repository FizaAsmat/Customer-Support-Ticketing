from django.db import models
from ..models.users import AppUser
from ..models.tickets import Ticket

class TicketPurpose(models.TextChoices):
    Ticket_Created ="Ticket Created"
    Ticket_Assigned = "Ticket Assigned"
    Comment="Comment"


class Notification(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    notifier = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name="sent_notifications"
    )
    purpose = models.CharField(
        max_length=30,
        choices=TicketPurpose.choices
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.purpose} - Ticket {self.ticket.id}"


class NotificationRecipient(models.Model):
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="recipients"
    )
    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    is_read = models.BooleanField(default=False)

    class Meta:
        unique_together = ("notification", "user")

    def __str__(self):
        return f"{self.user} notified"
