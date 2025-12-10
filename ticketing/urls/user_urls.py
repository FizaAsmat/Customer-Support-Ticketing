from django.urls import path
from ..views.user_views import (
    CustomerSignupView, AgentCreateView, LoginView,
    CustomerDashboardPageView, AgentDashboardPageView, LogoutView
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns=[
# Template rendering
    path('', CustomerDashboardPageView.as_view(), name="customer_dashboard_page"),
    path('', AgentDashboardPageView.as_view(), name="agent_dashboard_page"),

    path("signup/", CustomerSignupView.as_view(), name="customer-signup-api"),
    path("agents/new", AgentCreateView.as_view(), name="create-agent_api"),
    path("login/", LoginView.as_view(), name="login_api"),
    path("logout/", LogoutView.as_view(), name="logout"),

]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])