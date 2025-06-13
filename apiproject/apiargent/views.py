from decimal import Decimal

from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from .Serializer import AccountSerializer, LogSerializer
from .models import Account, Log

class PermissionSelfOrBanquier(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'banquier' or request.user.role == 'administrateur' or request.user.id == view.kwargs.get('id')

class PermissionBanquier(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'banquier' or request.user.role == 'administrateur'

class PermissionSelf(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.id == view.kwargs.get('id')

class PermissionSelfAccount(permissions.BasePermission):
    def has_permission(self, request, view):
        account_id = view.kwargs.get('id')
        try:
            account = Account.objects.get(pk=account_id)
            return request.user.id == account.user_id
        except Account.DoesNotExist:
            return False

class PermissionSelfAccountOrBanquier(permissions.BasePermission):
    def has_permission(self, request, view):
        account_id = view.kwargs.get('id')
        try:
            account = Account.objects.get(pk=account_id)
            return request.user.id == account.user_id or request.user.role == 'banquier' or request.user.role == 'administrateur'
        except Account.DoesNotExist:
            return False

class AccountView(APIView):
    def get(self, request, *args, **kwargs):
        users = Account.objects.all()
        serializer = AccountSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserAccountsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        id = request.user.id
        accounts = Account.objects.filter(user_id=id)
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserAccountsViewById(APIView):
    permission_classes = [permissions.IsAuthenticated, PermissionBanquier]

    def get(self, request, id, *args, **kwargs):
        try:
            accounts = Account.objects.filter(user_id=id).exclude(action="virement_recu")
        except Account.DoesNotExist:
            return Response({"res": "Object with id does not exist"},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AccountDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, PermissionSelfAccountOrBanquier]

    def get(self, request, id, *args, **kwargs):
        try:
            account = Account.objects.get(pk=id)
        except Account.DoesNotExist:
            return Response({"res": "Object with id does not exist"},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = AccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AccountBalanceUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, PermissionSelfAccount]

    def post(self, request, id, *args, **kwargs):
        try:
            account = Account.objects.get(pk=id)
        except Account.DoesNotExist:
            return Response({"res": "Object with id does not exist"},
                            status=status.HTTP_400_BAD_REQUEST)

        action = request.data.get("action")
        amount = Decimal(request.data.get("amount", 0))

        if action == "deposit":
            # Création d'un log pour le dépôt
            Log.objects.create(
                account=account,
                action='depot',
                montant=amount
            )
        elif action == "withdraw":
            if account.solde < amount:
                return Response({"res": "Insufficient funds"},
                                status=status.HTTP_400_BAD_REQUEST)
            # Création d'un log pour le retrait
            Log.objects.create(
                account=account,
                action='retrait',
                montant=amount
            )
        else:
            return Response({"res": "Invalid action"},
                            status=status.HTTP_400_BAD_REQUEST)

        account.save()
        serializer = AccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AccountLogView(APIView):
    permission_classes = [permissions.IsAuthenticated, PermissionSelfAccountOrBanquier]

    def get(self, request, id, nombre=None, *args, **kwargs):
        try:
            # Vérifier si le compte existe
            account = Account.objects.get(pk=id)

            # Récupérer tous les logs du compte triés par date (du plus récent au plus ancien)
            logs = Log.objects.filter(account=account).order_by('-date_action')

            # Limiter le nombre de résultats si un nombre est spécifié
            if nombre and isinstance(nombre, int) and nombre > 0:
                logs = logs[:nombre]

            serializer = LogSerializer(logs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Account.DoesNotExist:
            return Response({"res": "Compte introuvable"},
                            status=status.HTTP_404_NOT_FOUND)

class AccountVirementView(APIView):
    permission_classes = [permissions.IsAuthenticated, PermissionSelfAccountOrBanquier]

    def post(self, request, id, *args, **kwargs):
        source_account_id = id
        target_account_id = request.data.get("target_account_id")
        amount = Decimal(request.data.get("amount", 0))
        libele = request.data.get("libele")

        # Vérification que le montant est positif
        if amount <= 0:
            return Response({"res": "Le montant doit être positif"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            source_account = Account.objects.get(pk=source_account_id)
            target_account = Account.objects.get(pk=target_account_id)

            if source_account.solde < amount:
                return Response({"res": "Insufficient funds"},
                                status=status.HTTP_400_BAD_REQUEST)

            # Utiliser abs() pour garantir que le montant est positif (sécurité supplémentaire)
            amount = abs(amount)

            # Enregistrer les logs pour les deux comptes
            Log.objects.create(
                account=source_account,
                action='virement_envoye',
                montant=amount,
                cible=target_account,
                libele=libele
            )
            Log.objects.create(
                account=target_account,
                action='virement_recu',
                montant=amount,
                cible=source_account,
                libele=libele
            )

            source_account.save()
            target_account.save()

            return Response({"res": "Transfer successful"}, status=status.HTTP_200_OK)

        except Account.DoesNotExist:
            return Response({"res": "One or both accounts do not exist"},
                            status=status.HTTP_404_NOT_FOUND)

class PendingActionsView(APIView):
    permission_classes = [permissions.IsAuthenticated, PermissionBanquier]

    def get(self, request, *args, **kwargs):
        pending_logs = Log.objects.filter(date_valeur__isnull=True).exclude(action="virement_recu").order_by('date_action')
        serializer = LogSerializer(pending_logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ValidateActionView(APIView):
    permission_classes = [permissions.IsAuthenticated, PermissionBanquier]

    def post(self, request, id, *args, **kwargs):
        try:
            log = Log.objects.get(pk=id, date_valeur__isnull=True)
        except Log.DoesNotExist:
            return Response({"res": "Log not found or already processed"},
                            status=status.HTTP_404_NOT_FOUND)

        type_action = log.action

        if type_action == "virement_envoye":
            source_account = log.account
            target_account = log.cible
            amount = log.montant

            if source_account.solde < amount:
                return Response({"res": "Insufficient funds for the transfer"},
                                status=status.HTTP_400_BAD_REQUEST)

            source_account.solde -= amount
            target_account.solde += amount

            log.date_valeur = log.date_action

        elif type_action == "depot":
            account = log.account
            amount = log.montant

            account.solde += amount

            log.date_valeur = log.date_action

        elif type_action == "retrait":
            account = log.account
            amount = log.montant

            if account.solde < amount:
                return Response({"res": "Insufficient funds for the withdrawal"},
                                status=status.HTTP_400_BAD_REQUEST)

            account.solde -= amount

            log.date_valeur = log.date_action

        else:
            return Response({"res": "Invalid action type"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            source_account.save()
        except:
            pass
        try:
            target_account.save()
        except:
            pass
        try:
            account.save()
        except:
            pass
        log.save()

        return Response({"res": "Action validated successfully"}, status=status.HTTP_200_OK)

class DeclineActionView(APIView):
    permission_classes = [permissions.IsAuthenticated, PermissionBanquier]

    def post(self, request, id, *args, **kwargs):
        try:
            log = Log.objects.get(pk=id, date_valeur__isnull=True)
        except Log.DoesNotExist:
            return Response({"res": "Log not found or already processed"},
                            status=status.HTTP_404_NOT_FOUND)

        log.date_valeur = log.date_action

        log.save()

        return Response({"res": "Action refused and date set to current date"}, status=status.HTTP_200_OK)

class ChangeAccountStateView(APIView):
    permission_classes = [permissions.IsAuthenticated, PermissionBanquier]

    def post(self, request, id, *args, **kwargs):
        try:
            account = Account.objects.get(pk=id)
        except Account.DoesNotExist:
            return Response({"res": "Account not found"},
                            status=status.HTTP_404_NOT_FOUND)

        new_state = request.data.get("etat")
        if new_state not in ['actif', 'fermé']:
            return Response({"res": "Invalid account type"},
                            status=status.HTTP_400_BAD_REQUEST)

        account.statut = new_state
        account.save()

        serializer = AccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ListCreatedProcessAccountsView(APIView):
    permission_classes = [permissions.IsAuthenticated, PermissionBanquier]

    def get(self, request, *args, **kwargs):
        accounts = Account.objects.filter(statut='en_creation')
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RequestNewAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user_id = request.user.id
        data = {
            "user_id": user_id,
            "type_compte": request.data.get("type_compte"),
            "statut": 'en_creation'
        }
        serializer = AccountSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)