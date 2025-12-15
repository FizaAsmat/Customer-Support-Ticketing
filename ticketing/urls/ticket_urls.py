from django.urls import path
from ..views.ticket_views import CustomerTicketCreateView, TicketUpdateView

urlpatterns = [
    path("new/", CustomerTicketCreateView.as_view(), name="create-ticket"),
    # path('<int:pk>/show/', TicketShowView.as_view(), name='ticket_show'),
    path('<int:pk>/update/', TicketUpdateView.as_view(), name='ticket_update'),

]
