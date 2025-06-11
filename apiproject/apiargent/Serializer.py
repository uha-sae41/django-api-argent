from rest_framework import serializers
from .models import Account, Log

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "id",
            "user_id",
            "solde",
            "date_creation",
            "type_compte",
            "statut",
        ]

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = [
            "id",
            "account",
            "action",
            "montant",
            "date_action",
            "cible",
            "libele",
        ]
        read_only_fields = ['date_action']