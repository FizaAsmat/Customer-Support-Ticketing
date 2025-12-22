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
        on_delete=models.CASCADE,
        default="TODO"
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

        old_ticket = Ticket.objects.get(pk=self.pk) if is_update else None

        status_changed = (
                old_ticket and old_ticket.status_id != self.status_id
        )

        if self.status.status == "In-Progress":
            if not old_ticket or old_ticket.status.status != "In-Progress":
                self.start_time = timezone.now()

                if not self.deadline:
                    self.deadline = self.start_time + self.priority_id.duration

        if (
                self.deadline
                and not status_changed
                and self.status.status not in ["Resolved", "Closed", "Escalated"]
                and timezone.now() > self.deadline
        ):
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
            fields_to_track = [
                "title",
                "description",
                "priority_id",
                "status",
                "assignee_id",
                "ticket_category",
                "start_time",
                "deadline",
            ]

            for field in fields_to_track:
                old_value = getattr(old_ticket, field) if old_ticket else None
                new_value = getattr(self, field)

                if field in ["assignee_id", "creator_id"]:
                    old_value = f"{old_value.name} ({old_value.job_title})" if old_value else None
                    new_value = f"{new_value.name} ({new_value.job_title})" if new_value else None
                elif field == "status":
                    old_value = old_value.status if old_value else None
                    new_value = new_value.status if new_value else None
                elif field == "priority_id":
                    old_value = old_value.priority if old_value else None
                    new_value = new_value.priority if new_value else None
                elif isinstance(old_value, timezone.datetime) or isinstance(new_value, timezone.datetime):
                    old_value = old_value.strftime("%d %b %Y %H:%M:%S") if old_value else None
                    new_value = new_value.strftime("%d %b %Y %H:%M:%S") if new_value else None
                else:
                    old_value = str(old_value) if old_value is not None else None
                    new_value = str(new_value) if new_value is not None else None

                if old_value != new_value:
                    history_data[field] = {"old": old_value, "new": new_value}

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
        return f"History for Ticket {self.ticket.id} at {self.changes}"
