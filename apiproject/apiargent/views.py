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
        id = request.user.id
        accounts = Account.objects.filter(user_id=id)
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserAccountsViewById(APIView):
    #authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, PermissionBanquier]

    def get(self, request, id, *args, **kwargs):
        try:
            accounts = Account.objects.filter(user_id=id)
        except Account.DoesNotExist:
            return Response({"res": "Object with id does not exist"},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AccountDetailView(APIView):
    #authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, PermissionSelfOrBanquier]

    def get(self, request, id, *args, **kwargs):
        try:
            account = Account.objects.get(pk=id)
        except Account.DoesNotExist:
            return Response({"res": "Object with id does not exist"},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = AccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AccountBalanceUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, PermissionSelf]

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
    permission_classes = [permissions.IsAuthenticated, PermissionSelf]

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

# il faut créer une classe qui répond à l'endpoint /api/validate-action/type/id et ou le type sera soit virement_envoye ; depot ; retrait et aura une fonction différente sur les comptes
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

            # Vérifier que le solde du compte source est suffisant
            if source_account.solde < amount:
                return Response({"res": "Insufficient funds for the transfer"},
                                status=status.HTTP_400_BAD_REQUEST)

            # Effectuer le virement
            source_account.solde -= amount
            target_account.solde += amount

            # Mettre à jour la date de valeur du log
            log.date_valeur = log.date_action

        elif type_action == "depot":
            account = log.account
            amount = log.montant

            # Ajouter le montant au solde du compte
            account.solde += amount

            # Mettre à jour la date de valeur du log
            log.date_valeur = log.date_action

        elif type_action == "retrait":
            account = log.account
            amount = log.montant

            # Vérifier que le solde du compte est suffisant
            if account.solde < amount:
                return Response({"res": "Insufficient funds for the withdrawal"},
                                status=status.HTTP_400_BAD_REQUEST)

            # Retirer le montant du solde du compte
            account.solde -= amount

            # Mettre à jour la date de valeur du log
            log.date_valeur = log.date_action

        else:
            return Response({"res": "Invalid action type"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Enregistrer les modifications dans la base de données
        source_account.save()
        target_account.save()
        log.save()

        return Response({"res": "Action validated successfully"}, status=status.HTTP_200_OK)

# créer une classe qui va refuser les actions en attente et mettre comme date de valeur la 1ère date disponible par l'ordinateur
class DeclineActionView(APIView):
    permission_classes = [permissions.IsAuthenticated, PermissionBanquier]

    def post(self, request, id, *args, **kwargs):
        try:
            log = Log.objects.get(pk=id, date_valeur__isnull=True)
        except Log.DoesNotExist:
            return Response({"res": "Log not found or already processed"},
                            status=status.HTTP_404_NOT_FOUND)

        # Mettre à jour la date de valeur du log avec la date actuelle
        log.date_valeur = log.date_action

        # Enregistrer les modifications dans la base de données
        log.save()

        return Response({"res": "Action refused and date set to current date"}, status=status.HTTP_200_OK)