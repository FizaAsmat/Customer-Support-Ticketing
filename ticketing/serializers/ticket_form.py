from django import forms
from ..models.tickets import Ticket, TicketPriority
from ..models.users import AppUser, UserType

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "priority_id", "assignee_id"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields["assignee_id"].queryset = AppUser.objects.filter(
                role=UserType.AGENT,
                account_id=user.account_id
            )
        self.fields["priority_id"].queryset = TicketPriority.objects.all()

        # Optional: Make assignee optional
        self.fields["assignee_id"].required = False
