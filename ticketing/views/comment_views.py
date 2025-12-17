import uuid
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.utils import timezone
from ..models.tickets import Ticket
from ..models.comments import Thread, Comment
from ..serializers.comment_form import ThreadForm
from ..permissions import AccountAwareMixin


class TicketDetailView(AccountAwareMixin, View):
    def get(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)

        if request.user not in [ticket.creator_id, ticket.assignee_id]:
            return HttpResponseForbidden("You cannot view this ticket.")

        comments = (
            Thread.objects
            .filter(comment_entry__ticket=ticket)
            .order_by("-created_at")
        )

        form = ThreadForm()

        return render(
            request,
            "ticket_detail.html",
            {
                "ticket": ticket,
                "comments": comments,
                "form": form,
            }
        )

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)

        if request.user not in [ticket.creator_id, ticket.assignee_id]:
            return HttpResponseForbidden("You cannot comment on this ticket.")

        form = ThreadForm(request.POST)

        if form.is_valid():
            thread = form.save(commit=False)
            thread.commented_by = request.user

            if not request.POST.get("thread_group"):
                thread.thread_group = uuid.uuid4()
                thread.save()

                Comment.objects.create(
                    ticket=ticket,
                    thread=thread
                )

            else:
                thread.thread_group = request.POST.get("thread_group")
                thread.save()

            return redirect("ticket_detail", pk=ticket.pk)

        return redirect("ticket_detail", pk=ticket.pk)
