from django.db import models
from django.db.models import ForeignKey, CASCADE
from django.db.models.constraints import UniqueConstraint


class UserType(models.TextChoices):
    AGENT ="Agent","Agent"
    CUSTOMER = "Customer","Customer"


class Account(models.Model):
    portal=models.CharField(max_length=255,unique=True)


class AppUser(models.Model):
    account_id=ForeignKey(Account,on_delete=CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    password = models.CharField(max_length=72)
    job_title = models.CharField(max_length=20)
    role = models.CharField(
        choices=UserType.choices,
        default=UserType.CUSTOMER
    )

    class Meta:
        constraints=[
            UniqueConstraint(fields=('account_id','email'),name='unique_agent')
        ]