from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from ..models.notifications import NotificationRecipient
from ..permissions import AccountAwareMixin

@method_decorator(csrf_exempt, name="dispatch")
class MarkNotificationsReadView(AccountAwareMixin, View):

    def post(self, request):
        NotificationRecipient.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

        return JsonResponse({"status": "success"})