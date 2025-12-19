from django import forms
from ..models.tickets import Ticket, TicketPriority, TicketStatus
from ..models.users import AppUser, UserType
from ..utils.status_transition import get_allowed_transitions


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
        fields = [
            "title",
            "description",
            "ticket_category",
            "priority_id",
            "assignee_id",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field_name in ["duration", "ticket_category", "assignee_id", "priority_id"]:
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

        self.fields["priority_id"].queryset = TicketPriority.objects.all()
        self.fields["priority_id"].label = "Priority"
        self.fields["priority_id"].empty_label = None
        self.fields["priority_id"].required = True

        self.fields["duration"].choices = [("", "Select Duration")] + self.DEFAULT_CHOICES
        self.fields["duration"].required = False

        if user:
            agents = AppUser.objects.filter(
                role=UserType.AGENT,
                account_id=user.account_id,
                is_active=True,
            )
            self.fields["assignee_id"] = forms.ModelChoiceField(
                queryset=agents,
                required=False,
                label="Assignee",
                empty_label="Select Assignee",
                widget=forms.Select(attrs={"class": "form-select"})
            )

            if self.instance and self.instance.assignee_id:
                self.fields["assignee_id"].initial = self.instance.assignee_id

            self.fields["assignee_id"].label_from_instance = lambda obj: f"{obj.name} ({obj.job_title})"

            categories = (
                AppUser.objects.filter(
                    role=UserType.AGENT,
                    account_id=user.account_id,
                    is_active=True
                )
                .exclude(job_title__isnull=True)
                .exclude(job_title="")
                .values_list("job_title", flat=True)
                .distinct()
            )
            self.fields["ticket_category"] = forms.ChoiceField(
                choices=[(c, c) for c in categories],
                required=True,
                label="Category"
            )

class TicketUpdateForm(forms.ModelForm):
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
            "ticket_category": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        self.ticket = kwargs.pop("ticket")
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        self.fields["priority_id"].queryset = TicketPriority.objects.all()
        self.fields["priority_id"].label = "Priority"
        self.fields["priority_id"].empty_label = None
        self.fields["priority_id"].required = True
        if self.ticket.priority_id:
            self.fields["priority_id"].initial = self.ticket.priority_id
        self.fields["priority_id"].widget.attrs.update({"class": "form-select"})

        default_choice = ""
        if self.ticket.priority_id and self.ticket.priority_id.duration:
            total_seconds = int(self.ticket.priority_id.duration.total_seconds())

            if total_seconds < 3600:
                minutes = total_seconds // 60
                default_choice = f"{minutes}m"
            elif total_seconds < 86400:
                hours = total_seconds // 3600
                default_choice = f"{hours}h"
            else:
                days = total_seconds // 86400
                default_choice = f"{days}d"

        self.fields["duration"].choices = (
            [("", "Select Duration")] +
            [(default_choice, f"From Priority ({default_choice})")] +
            self.DEFAULT_CHOICES
        )
        self.fields["duration"].initial = ""
        self.fields["duration"].widget.attrs.update({"class": "form-select"})

        agents = AppUser.objects.filter(role=UserType.AGENT, account_id=self.user.account_id, is_active=True)
        self.fields["assignee_id"] = forms.ModelChoiceField(
            queryset=agents,
            required=False,
            empty_label="Select Assignee",
            label="Assignee",
            widget=forms.Select(attrs={"class": "form-select"})
        )
        self.fields["assignee_id"].initial = self.ticket.assignee_id
        self.fields["assignee_id"].label_from_instance = lambda obj: f"{obj.name} ({obj.job_title})"

        categories = (
            AppUser.objects.filter(role=UserType.AGENT, account_id=self.user.account_id, is_active=True)
            .exclude(job_title__isnull=True)
            .exclude(job_title="")
            .values_list("job_title", flat=True)
            .distinct()
        )
        self.fields["ticket_category"] = forms.ChoiceField(
            choices=[(c, c) for c in categories],
            required=True,
            label="Category",
            widget=forms.Select(attrs={"class": "form-select"})
        )
        self.fields["ticket_category"].initial = self.ticket.ticket_category

        allowed_statuses = get_allowed_transitions(self.ticket.status.status)
        allowed_statuses.append(self.ticket.status.status)
        self.fields["status"] = forms.ModelChoiceField(
            queryset=TicketStatus.objects.filter(status__in=allowed_statuses),
            initial=self.ticket.status,
            widget=forms.Select(attrs={"class": "form-select"}),
            label="Status",
            empty_label=None
        )

        self.fields["title"].initial = self.ticket.title
        self.fields["description"].initial = self.ticket.description
        self.fields["description"].widget.attrs.update({"rows": 4})

    def clean(self):
        cleaned_data = super().clean()
        new_status = cleaned_data.get("status")
        assignee = cleaned_data.get("assignee_id") or self.ticket.assignee_id

        if new_status and new_status.status == "In-Progress" and not assignee:
            raise forms.ValidationError(
                "Ticket must have an assignee before it can be moved to In-Progress."
            )
        return cleaned_data
