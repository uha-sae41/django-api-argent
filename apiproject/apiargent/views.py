from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from .Serializer import AccountSerializer
from .models import Account

class AccountView(APIView):
    def get(self, request, *args, **kwargs):
        users = Account.objects.all()
        serializer = AccountSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = {
            "user_id": request.data.get("user_id"),
            "solde": request.data.get("solde"),
            "date_creation": request.data.get("date_creation"),
            "type_compte": request.data.get("type_compte"),
            "statut": request.data.get("statut"),
        }
        serializer = AccountSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# créer une classe qui permet de lister les comptes de l'utilisateur connecté
class UserAccountsView(APIView):
    #authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = request.user.id
        accounts = Account.objects.filter(user_id=user_id)
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AccountDetailView(APIView):
    #authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            account = Account.objects.get(pk=id)
        except Account.DoesNotExist:
            return Response({"res": "Object with id does not exist"},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = AccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)