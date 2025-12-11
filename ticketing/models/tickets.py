from django.db import models
from django.db.models import ForeignKey, CASCADE
from .users import AppUser,UserType
from django.utils import timezone

class TicketStatus(models.Model):
    status=models.CharField(max_length=70)

class TicketPriority(models.Model):
    priority=models.CharField(max_length=6)
    duration=models.DurationField()

class Ticket(models.Model):
    creator_id = models.ForeignKey(AppUser, related_name="assigned_by", on_delete=models.CASCADE, limit_choices_to={'role': UserType.CUSTOMER})
    title = models.CharField(unique=True, max_length=255)
    description = models.TextField()
    priority_id = models.ForeignKey(TicketPriority, on_delete=models.CASCADE)
    status = models.ForeignKey(TicketStatus, default="TODO", on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    assignee_id = models.ForeignKey(AppUser, related_name="assigned_to", null=True, blank=True, on_delete=models.SET_NULL, limit_choices_to={'role': UserType.AGENT})


    def save(self, *args, **kwargs):
        if self.assignee_id and not self.start_time:
            self.start_time = timezone.now()
            self.deadline = self.start_time + self.priority_id.duration

        super().save(*args, **kwargs)

class TicketHistory(models.Model):
    ticket_id=ForeignKey(Ticket, on_delete=models.CASCADE)
    previous_state=ForeignKey(TicketStatus, default="TODO", related_name="old_status", on_delete=CASCADE)
    prev_description=models.TextField()
    current_state=ForeignKey(TicketStatus, related_name="new_status", on_delete=CASCADE)
    current_description=models.TextField()
    updated_by=ForeignKey(AppUser,on_delete=CASCADE)
    changed_at=models.DateTimeField(auto_now_add=True)

    def save(self,*args,**kwargs):
        self.pk=None
        super().save(*args,**kwargs)