from django import forms
from ..models.comments import Thread

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "Write a comment...",
                    "class": "form-control",
                }
            )
        }
