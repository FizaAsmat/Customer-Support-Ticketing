from django.views import View
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.utils import timezone
from ..serializers.ticket_form import TicketForm, TicketUpdateForm
from ..models.tickets import Ticket, TicketStatus, TicketHistory
from ..permissions import CustomerRequiredMixin, AccountAwareMixin
from django.contrib import messages
from ..models.users import AppUser
from ..models.comments import Thread, Comment
from ..serializers.comment_form import ThreadForm
from ..utils.status_transition import get_allowed_transitions
from ..utils.notifications_utils import (
    notify_ticket_created,
    notify_ticket_assigned,
    notify_ticket_status_updated,
    notify_comment_added,
    notify_reply_added,
)

class CustomerTicketCreateView(CustomerRequiredMixin, AccountAwareMixin, View):
    login_url = "/login/"

    def get(self, request):
        form = TicketForm(user=request.user)
        return render(request, "ticket_form.html", {"form": form})

    def post(self, request):
        form = TicketForm(request.POST, user=request.user)

        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.creator_id = request.user

            ticket.status = TicketStatus.objects.get(status="TODO")

            duration_map = {
                "1h": timedelta(hours=1),
                "4h": timedelta(hours=4),
                "8h": timedelta(hours=8),
                "1d": timedelta(days=1),
                "2d": timedelta(days=2),
            }
            selected_duration = form.cleaned_data.get("duration")
            sla_duration = duration_map.get(selected_duration)
            if not sla_duration and ticket.priority_id:
                sla_duration = ticket.priority_id.duration

            if ticket.assignee_id and sla_duration:
                ticket.start_time = timezone.now()
                ticket.deadline = ticket.start_time + sla_duration
                ticket.status = TicketStatus.objects.get(status="In-Progress")

            ticket.save(updated_by=request.user)
            notify_ticket_created(ticket, request.user)

            return redirect("customer_dashboard_page")

        return render(request, "ticket_form.html", {"form": form})



class TicketUpdateView(CustomerRequiredMixin, View):
    login_url = "/login/"

    def get_ticket(self, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        if ticket.creator_id.account_id != self.request.user.account_id:
            return None
        return ticket

    def get(self, request, pk):
        ticket = self.get_ticket(pk)
        if not ticket:
            return HttpResponseForbidden("You cannot update this ticket.")
        form = TicketUpdateForm(instance=ticket, ticket=ticket, user=request.user)
        return render(request, "ticket_update.html", {"form": form, "ticket": ticket})

    def post(self, request, pk):
        ticket = self.get_ticket(pk)
        if not ticket:
            return HttpResponseForbidden("Only customers can update tickets.")

        old_status = ticket.status

        form = TicketUpdateForm(
            request.POST,
            instance=ticket,
            ticket=ticket,
            user=request.user
        )

        if form.is_valid():
            updated_ticket = form.save(commit=False)
            if updated_ticket.assignee_id and not updated_ticket.assignee_id.is_active:
                form.add_error(
                    "assignee_id",
                    "Selected assignee is inactive. Please choose an active agent."
                )
                return render(request, "ticket_update.html", {"form": form, "ticket": ticket})

            if (
                    updated_ticket.status.status == "In-Progress"
                    and old_status.status != "In-Progress"
                    and updated_ticket.assignee_id
            ):
                updated_ticket.start_time = timezone.now()
                updated_ticket.deadline = timezone.now() + updated_ticket.priority_id.duration

            updated_ticket.save(updated_by=request.user)

            if old_status != updated_ticket.status:
                notify_ticket_status_updated(updated_ticket, request.user,old_status)
            return redirect("customer_dashboard_page")

        return render(request, "ticket_update.html", {"form": form, "ticket": ticket})


def Assign_ticket(request, pk):
    if request.method == "POST":

        user_id = request.session.get("user_id")
        if not user_id:
            messages.error(request, "Please login to assign tickets.")
            return redirect("login")

        user = get_object_or_404(AppUser, id=user_id)
        ticket = get_object_or_404(Ticket, pk=pk)

        if ticket.assignee_id is None:
            ticket.assignee_id = user
            ticket.save(updated_by=user)

            notify_ticket_assigned(ticket, user)
            messages.success(request, f"Ticket '{ticket.title}' assigned to you.")
        else:
            messages.warning(request, f"Ticket '{ticket.title}' is already assigned.")

    return redirect("agent_dashboard_page")


class TicketDetailView(AccountAwareMixin, View):
    login_url = "/login/"

    def get(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)

        if request.user.account_id != ticket.creator_id.account_id:
            return HttpResponseForbidden("You cannot view this ticket.")

        comments = Thread.objects.filter(
            comment_entry__ticket=ticket
        ).order_by("-created_at")

        history = TicketHistory.objects.filter(
            ticket=ticket
        ).select_related("updated_by").order_by("-updated_at")

        form = ThreadForm()

        current_status = ticket.status.status
        allowed = get_allowed_transitions(current_status)

        allowed.append(current_status)

        if "In-Progress" in allowed and not ticket.assignee_id:
            allowed.remove("In-Progress")

        allowed_statuses = TicketStatus.objects.filter(
            status__in=allowed
        )

        replies_dict = {}
        for comment in comments:
            replies = Thread.objects.filter(
                thread_group=comment.thread_group
            ).exclude(id=comment.id).order_by("created_at")
            replies_dict[comment.id] = replies

        return render(request, "ticket_detail.html", {
            "ticket": ticket,
            "comments": comments,
            "history": history,
            "replies_dict": replies_dict,
            "form": form,
            "allowed_statuses": allowed_statuses,
        })

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)

        user_id = request.session.get("user_id")
        if not user_id:
            return HttpResponseForbidden("Login required")

        user = get_object_or_404(AppUser, id=user_id)

        if user.account_id != ticket.creator_id.account_id:
            return HttpResponseForbidden("You cannot comment on this ticket.")

        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.commented_by = user
            thread.save()

            comment=Comment.objects.create(ticket=ticket, thread=thread)

            notify_comment_added(comment, user)

            messages.success(request, "Comment added successfully.")
        return redirect("ticket_detail", pk=ticket.pk)

class UpdateTicketStatusView(AccountAwareMixin, View):
    login_url = "/login/"

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)

        old_status = ticket.status
        new_status_id = request.POST.get("status")
        if not new_status_id:
            messages.error(request, "No status selected.")
            return redirect("ticket_detail", pk=pk)

        new_status = get_object_or_404(TicketStatus, pk=new_status_id)

        current_status = old_status.status
        allowed = get_allowed_transitions(current_status)
        allowed.append(current_status)

        if new_status.status not in allowed:
            messages.error(
                request,
                f"Invalid status transition from {current_status} to {new_status.status}."
            )
            return redirect("ticket_detail", pk=pk)

        if new_status.status == "In-Progress" and not ticket.assignee_id:
            messages.error(
                request,
                "Ticket must have an assignee before moving to In-Progress."
            )
            return redirect("ticket_detail", pk=pk)

        ticket.status = new_status
        ticket.save(updated_by=request.user)

        if old_status != new_status:
            notify_ticket_status_updated(ticket, request.user,old_status)

        messages.success(request, f"Ticket status updated to {new_status}.")
        return redirect("ticket_detail", pk=pk)


class ReplyCommentView(AccountAwareMixin, View):
    login_url = "/login/"

    def post(self, request, thread_id):
        original_thread = get_object_or_404(Thread, id=thread_id)
        ticket = Comment.objects.get(thread=original_thread).ticket

        reply_body = request.POST.get("reply")
        if reply_body:
            reply=Thread.objects.create(
                body=reply_body,
                commented_by=request.user,
                thread_group=original_thread.thread_group
            )
            notify_reply_added(reply, request.user)

        return redirect("ticket_detail", pk=ticket.pk)