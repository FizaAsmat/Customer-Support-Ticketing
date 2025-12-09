from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from ..permissions import IsCustomer
from ..serializers.user_serial import CustomerSignupSerializer,AgentCreateSerializer,LoginSerializer
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models.users import UserType

class CustomerSignupView(APIView):
    permission_classes = [AllowAny]

    def post(self,request):
        serializer =CustomerSignupSerializer(data=request.data)

        if serializer.is_valid():
            user=serializer.save()
            return Response({"message":"Customer registered successfully","user_id":user.id},
                            status=status.HTTP_201_CREATED)

        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


class AgentCreateView(APIView):
    permission_classes = IsAuthenticated, IsCustomer

    def post(self,request):
        serializer=AgentCreateSerializer(data=request.data, context={"request":request})

        if serializer.is_valid():
            agent=serializer.save()
            return Response({"message":"Agent created successfully", "agent_id":agent.id},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self,request):
        serializer=LoginSerializer(data=request.data)

        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class LoginPageView(View):
    def get(self, request):
        return render(request, "login.html")


class SignupPageView(View):
    def get(self, request):
        return render(request, "signup.html")


class CustomerDashboardPageView(LoginRequiredMixin, View):
    login_url = "/app/login/"  # <- your login page route
    redirect_field_name = "next"

    def get(self, request):
        if request.user.role != UserType.CUSTOMER:
            return redirect("agent_dashboard_page")
        return render(request, "customer_dashboard.html", {"user": request.user})


class AgentDashboardPageView(LoginRequiredMixin, View):
    login_url = "/app/login/"  # <- your login page route
    redirect_field_name = "next"  # optional, default is "next"
    def get(self, request):
        if request.user.role != UserType.AGENT:
            return redirect("customer_dashboard_page")
        return render(request, "agent_dashboard.html", {"user": request.user})
