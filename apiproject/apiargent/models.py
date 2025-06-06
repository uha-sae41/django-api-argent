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