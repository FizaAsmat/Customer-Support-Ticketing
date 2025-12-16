from django.db import models
from .users import AppUser
from .tickets import Ticket
from django.core.exceptions import ValidationError

class Thread(models.Model):
    thread_group = models.UUIDField()
    body = models.TextField(max_length=450)
    commented_by = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        comment = Comment.objects.filter(thread=self).first()
        if comment:
            ticket = comment.ticket
            if self.commented_by not in [ticket.creator_id, ticket.assignee_id]:
                raise ValidationError(
                    "Only the ticket creator or assignee can comment or reply."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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
