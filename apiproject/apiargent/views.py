from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .Serializer import AccountSerializer
from .models import Account

class AccountView(APIView):
    def get(self, request, *args, **kwargs):
        users = Account.objects.all()
        serializer = AccountSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)