from django.db import models
from django.utils import timezone
from .users import AppUser, UserType


class TicketStatus(models.Model):
    status = models.CharField(max_length=70, unique=True)

    def __str__(self):
        return self.status


class TicketPriority(models.Model):
    priority = models.CharField(max_length=6)
    duration = models.DurationField()

    def __str__(self):
        return self.priority


class Ticket(models.Model):
    creator_id = models.ForeignKey(
        AppUser,
        related_name="assigned_by",
        on_delete=models.CASCADE,
        limit_choices_to={'role': UserType.CUSTOMER}
    )
    title = models.CharField(unique=True, max_length=255)
    description = models.TextField()
    priority_id = models.ForeignKey(TicketPriority, on_delete=models.CASCADE)
    status = models.ForeignKey(
        TicketStatus,
        on_delete=models.CASCADE
    )
    start_time = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    ticket_category = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    assignee_id = models.ForeignKey(
        AppUser,
        related_name="assigned_to",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'role': UserType.AGENT}
    )

    def save(self, *args, **kwargs):
        updated_by = kwargs.pop("updated_by", None)
        is_update = self.pk is not None

        # Get old ticket if updating
        if is_update:
            old_ticket = Ticket.objects.get(pk=self.pk)
            old_status = old_ticket.status.status
            old_description = old_ticket.description
        else:
            old_ticket = None
            old_status = None
            old_description = None

        # Initial assignment logic
        if self.assignee_id and not self.start_time:
            self.start_time = timezone.now()
            self.deadline = self.start_time + self.priority_id.duration
            # Set status to IN_PROGRESS when assigned
            try:
                self.status = TicketStatus.objects.get(status="In-Progress")
            except TicketStatus.DoesNotExist:
                pass  # handle if status not present

        #SLA Escalation
        if self.deadline and self.status.status not in ["Resolved", "Closed", "Escalated"]:
            if timezone.now() > self.deadline:
                try:
                    self.status = TicketStatus.objects.get(status="Escalated")
                except TicketStatus.DoesNotExist:
                    pass

        if self.status.status == "Waiting-For-Customer":
            inactivity_limit_days = 1
            last_change = old_ticket.changed_at if old_ticket else self.created_at
            if (timezone.now() - last_change).days >= inactivity_limit_days:
                try:
                    self.status = TicketStatus.objects.get(status="Closed")
                except TicketStatus.DoesNotExist:
                    pass

        super().save(*args, **kwargs)

        if is_update and updated_by:
            history_data = {}

            if old_status != self.status.status:
                history_data["status"] = {
                    "old": old_status,
                    "new": self.status.status,
                }

            if old_description != self.description:
                history_data["description"] = {
                    "old": old_description,
                    "new": self.description
                }

            if history_data:
                TicketHistory.objects.create(
                    ticket=self,
                    updated_by=updated_by,
                    changes=history_data
                )

    def __str__(self):
        return f"{self.title} ({self.status.status})"


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="history")
    updated_by = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"History for Ticket {self.ticket.id} at {self.changed_at}"
