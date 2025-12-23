from django.db import models
from django.db.models.constraints import UniqueConstraint

class UserType(models.TextChoices):
    AGENT ="Agent","Agent"
    CUSTOMER = "Customer","Customer"
    SYSTEM = "System","System"

class Account(models.Model):
    portal=models.CharField(max_length=255,unique=True)

class AppUser(models.Model):
    account_id=models.ForeignKey(Account,on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    password = models.CharField(max_length=72)
    job_title = models.CharField(max_length=20)
    role = models.CharField(
        choices=UserType.choices,
        default=UserType.CUSTOMER
    )
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints=[
            UniqueConstraint(fields=('account_id','email'),name='unique_agent')
        ]