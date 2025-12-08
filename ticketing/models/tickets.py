from django.db import models
from django.db.models import ForeignKey, CASCADE
from .users import AppUser

class TicketStatus(models.Model):
    status=models.CharField(max_length=70)

class TicketPriority(models.Model):
    priority=models.CharField(max_length=6)
    time=models.TimeField()

class Ticket(models.Model):
    customer_id=ForeignKey(AppUser,on_delete=models.CASCADE)
    title=models.CharField(unique=True,max_length=255)
    description=models.TextField()
    priority_id=ForeignKey(TicketPriority,on_delete=CASCADE)
    status=ForeignKey(TicketStatus,default="TODO",on_delete=CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)

class TicketHistory(models.Model):
    ticket_id=ForeignKey(Ticket,on_delete=models.CASCADE)
    previous_state=ForeignKey(TicketStatus,default="TODO",related_name="old_status",on_delete=CASCADE)
    prev_description=models.TextField()
    current_state=ForeignKey(TicketStatus,related_name="new_status",on_delete=CASCADE)
    current_description=models.TextField()
    changed_by=ForeignKey(AppUser,on_delete=CASCADE)
    changed_at=models.DateTimeField(auto_now_add=True)
    version=models.IntegerField(default=1)

    def save(self,*args,**kwargs):
        if self.pk:
            old=TicketHistory.objects.get(pk=self.pk)
            self.pk=None
            self.version=old.version+1
        super().save(*args,**kwargs)