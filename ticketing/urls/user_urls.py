from django.urls import path
from ..views.user_views import (
    CustomerSignupView, AgentCreateView, LoginView, LoginPageView,
    SignupPageView, CustomerDashboardPageView, AgentDashboardPageView
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns=[
# Template rendering
    path("login/", LoginPageView.as_view(), name="login_page"),
    path("signup/", SignupPageView.as_view(), name="signup_page"),
    path("customer_dashboard/", CustomerDashboardPageView.as_view(), name="customer_dashboard_page"),
    path("agent-dashboard/", AgentDashboardPageView.as_view(), name="agent_dashboard_page"),

    path("api/signup/", CustomerSignupView.as_view(), name="customer-signup-api"),
    path("create-agent/", AgentCreateView.as_view(), name="create-agent_api"),
    path("api/login/", LoginView.as_view(), name="login_api"),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])