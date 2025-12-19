from django.urls import path
from ..views.user_views import (
    CustomerSignupView, AgentCreateView, LoginView,
    CustomerDashboardPageView, AgentDashboardPageView, LogoutView, AgentSoftDeleteView
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns=[
    path('', CustomerDashboardPageView.as_view(), name="customer_dashboard_page"),
    path('home/', AgentDashboardPageView.as_view(), name="agent_dashboard_page"),
    path("signup/", CustomerSignupView.as_view(), name="customer-signup-api"),
    path("agents/new", AgentCreateView.as_view(), name="create-agent_api"),
    path("login/", LoginView.as_view(), name="login_api"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('agent/<int:agent_id>/delete/', AgentSoftDeleteView.as_view(), name='agent_soft_delete'),

]