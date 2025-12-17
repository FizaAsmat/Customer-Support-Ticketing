import uuid
from django.db import models
from .users import AppUser
from .tickets import Ticket

class Thread(models.Model):
    thread_group = models.UUIDField(default=uuid.uuid4, editable=False)
    body = models.TextField(max_length=450)
    commented_by = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def replies(self):
        return Thread.objects.filter(thread_group=self.thread_group).exclude(id=self.id).order_by("created_at")


class Comment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    thread = models.OneToOneField(
        "Thread",
        on_delete=models.CASCADE,
        related_name="comment_entry"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment Thread {self.thread.id} for Ticket {self.ticket.id}"
