from .models.notifications import NotificationRecipient

def notifications_processor(request):
    user = getattr(request, "user", None)

    if not user or not getattr(user, "id", None):
        return {"notifications": [], "unread_count": 0}

    qs = NotificationRecipient.objects.filter(
        user_id=user.id
    ).select_related(
        "notification", "notification__ticket"
    ).order_by("-notification__sent_at")

    unread_count = qs.filter(is_read=False).count()
    notifications = qs[:10]

    return {
        "notifications": notifications,
        "unread_count": unread_count
    }
