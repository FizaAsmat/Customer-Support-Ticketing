from ..views.notification_views import MarkNotificationsReadView
from django.urls import path

urlpatterns = [
    path(
        "notifications/mark-read/",
        MarkNotificationsReadView.as_view(),
        name="mark_notifications_read"
    ),
]
