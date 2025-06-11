from django.db import models

class Account(models.Model):
    user_id = models.IntegerField(verbose_name="ID de l'utilisateur")
    solde = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Solde du compte")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création du compte")
    type_compte = models.CharField(max_length=50, verbose_name="Type de compte", choices=[
        ('epargne', 'Épargne'),
        ('courant', 'Courant')
    ], default='courant')
    statut = models.CharField(max_length=20, verbose_name="Statut du compte", choices=[
        ('actif', 'Actif'),
        ('fermé', 'Fermé')
    ], default='actif')

    def __str__(self):
        return f"Compte de l'utilisateur {self.user_id} - Solde: {self.solde} - Type: {self.type_compte} - Statut: {self.statut}"

    def __repr__(self):
        return f"Account(user_id={self.user_id}, solde={self.solde}, type_compte={self.type_compte}, statut={self.statut})"

class Log(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='logs', verbose_name="Compte associé")
    action = models.CharField(max_length=50, verbose_name="Action effectuée", choices=[
        ('depot', 'Dépôt'),
        ('retrait', 'Retrait'),
        ('virement_recu', 'Virement reçu'),
        ('virement_envoye', 'Virement envoyé'),
    ])
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant de l'action")
    date_action = models.DateTimeField(auto_now_add=True, verbose_name="Date de l'action")
    date_valeur = models.DateTimeField(null=True, blank=True, verbose_name="Date de valeur de l'action")
    cible = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs_cible', verbose_name="Compte cible (pour les virements)")
    libele = models.CharField(max_length=255, null=True, blank=True, verbose_name="Libellé de l'action")

    def __str__(self):
        return f"{self.action} de {self.montant} sur le compte {self.account.user_id} le {self.date_action}"

    def __repr__(self):
        return f"Log(account={self.account.user_id}, action={self.action}, montant={self.montant}, date_action={self.date_action}, cible={self.cible.user_id if self.cible else 'None'})"