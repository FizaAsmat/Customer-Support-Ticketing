from django.urls import path
from ..views.ticket_views import CustomerTicketCreateView

urlpatterns = [
    path("new/", CustomerTicketCreateView.as_view(), name="create-ticket"),
]
