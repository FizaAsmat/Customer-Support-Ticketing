from django.urls import path
from ..views.ticket_views import CustomerTicketCreateView, TicketUpdateView, Assign_ticket, TicketDetailView,UpdateTicketStatusView,ReplyCommentView

urlpatterns = [
    path("new/", CustomerTicketCreateView.as_view(), name="create-ticket"),
    # path('<int:pk>/show/', TicketShowView.as_view(), name='ticket_show'),
    path('<int:pk>/update/', TicketUpdateView.as_view(), name='ticket_update'),
    path("ticket/<int:pk>/assign-to-me/", Assign_ticket, name="assign_ticket_to_me"),
    path("ticket/<int:pk>/", TicketDetailView.as_view(), name="ticket_detail"),
    path("ticket/<int:pk>/update_status/", UpdateTicketStatusView.as_view(), name="update_ticket_status"),
    path("comment/<int:thread_id>/reply/", ReplyCommentView.as_view(), name="reply_comment"),
]
