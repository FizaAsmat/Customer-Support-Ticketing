from django import forms
from ..models.tickets import Ticket, TicketPriority, TicketStatus
from ..models.users import AppUser, UserType

class TicketForm(forms.ModelForm):
    DEFAULT_CHOICES = [
        ("1h", "1 Hour"),
        ("4h", "4 Hours"),
        ("8h", "8 Hours"),
        ("1d", "1 Day"),
        ("2d", "2 Days"),
    ]
    duration = forms.ChoiceField(
        choices=[],
        required=False,
        label="SLA Duration"
    )

    class Meta:
        model = Ticket
        fields = ["title", "description", "priority_id", "ticket_category", "assignee_id"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["priority_id"].queryset = TicketPriority.objects.all()
        self.fields["priority_id"].label = "Priority"
        self.fields["priority_id"].empty_label = None

        default_choice = ""
        priority_instance = getattr(self.instance, "priority_id", None)
        if priority_instance and priority_instance.duration:
            total_hours = int(priority_instance.duration.total_seconds() // 3600)
            if total_hours < 24:
                default_choice = f"{total_hours}h"
            else:
                default_choice = f"{total_hours // 24}d"

        self.fields["duration"].choices = [(default_choice, f"From Priority ({default_choice})")] + self.DEFAULT_CHOICES
        self.fields["duration"].required=False

        if user:
            agents = AppUser.objects.filter(
                role=UserType.AGENT, account_id=user.account_id
            ).values("id", "name", "job_title")
            agent_choices = [(agent["id"], f'{agent["name"]} ({agent["job_title"]})') for agent in agents]

            self.fields["assignee_id"] = forms.ChoiceField(
                choices=[("", "Select Agent")] + agent_choices,
                required=False,
                label="Assignee"
            )
        self.fields["assignee_id"].required=False
        if user:
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

        self.fields["title"].label = "Title"
        self.fields["description"].label = "Description"
        self.fields["description"].widget.attrs.update({"rows": 4})

class TicketUpdateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            "title",
            "description",
            "priority_id",
            "status",
            "assignee_id",
            "ticket_category",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "priority_id": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "assignee_id": forms.Select(attrs={"class": "form-select"}),
            "ticket_category": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.ticket = kwargs.pop("ticket")
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        allowed_statuses = self.get_allowed_transitions()

        allowed_statuses.append(self.ticket.status.status)

        self.fields["status"].queryset = TicketStatus.objects.filter(
            status__in=allowed_statuses
        )

        self.fields["status"].initial = self.ticket.status

    def get_allowed_transitions(self):
        transitions = {
            "TODO": ["In-Progress"],
            "In-Progress": ["Waiting-For-Customer", "Resolved"],
            "Waiting-For-Customer": ["In-Progress", "Resolved"],
            "Resolved": ["Closed"],
            "Closed": [],
            "Escalated": ["In-Progress"],
        }
        return transitions.get(self.ticket.status.status, [])
