from django import forms
from ..models.tickets import Ticket, TicketPriority, TicketStatus
from ..models.users import AppUser, UserType


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "priority_id", "ticket_category", "assignee_id"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        #Assignee
        if user:
            self.fields["assignee_id"].queryset = AppUser.objects.filter(
                role=UserType.AGENT,
                account_id=user.account_id
            ).values_list("j")
            self.fields["assignee_id"].required = False

            job_titles = (
                AppUser.objects.filter(role=UserType.AGENT, account_id=user.account_id)
                .exclude(job_title__isnull=True)
                .exclude(job_title="")
                .values_list("job_title", flat=True)
                .distinct()
            )
            self.fields["ticket_category"] = forms.ChoiceField(
                choices=[(jt, jt) for jt in job_titles],
                required=True,
                label="Ticket Category"
            )

        #Priority
        self.fields["priority_id"].queryset = TicketPriority.objects.all()
        self.fields["priority_id"].label = "Priority"

        self.fields["title"].label = "Title"
        self.fields["description"].label = "Description"
        self.fields["description"].widget.attrs.update({"rows": 4})


class TicketUpdateForm(forms.Form):
    status = forms.ModelChoiceField(queryset=TicketStatus.objects.all(), required=True)
    description = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        self.ticket = kwargs.pop("ticket")
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["status"].queryset = TicketStatus.objects.filter(
            status__in=self.get_allowed_transitions()
        )

    def get_allowed_transitions(self):
        current = self.ticket.status.status
        transitions = {
            "TODO": ["In-Progress"],
            "In-Progress": ["Waiting-For-Customer", "Resolved"],
            "Waiting-For-Customer": ["In-Progress", "Resolved"],
            "Resolved": ["Closed"],
            "Closed": [],
            "Escalated": ["In-Progress"],
        }
        return transitions.get(current, [])
