# coding=UTF-8
from django.db import models
from django.forms import ModelForm, Textarea
from decimal import Decimal
from django.core import validators
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

# Create your models here.
class Cyber(models.Model):
	nom = models.CharField(max_length=200)
	identifiant = models.CharField(max_length=50)
	monnaie = models.CharField(max_length=200)
	user = models.ForeignKey(User, unique=True)
	def __unicode__(self):
		return self.nom

class Utilisateur(models.Model):
	login = models.CharField(max_length=200)
	identifiant = models.CharField(max_length=50)
	type_compte = models.CharField('Type de compte', max_length=200, choices = (('utilisateur', 'Utilisateur'), ('machine', 'Machine')))
	date_naissance = models.DateField('Date de naissance', null=True)
	derniere_connexion = models.DateTimeField('Dernière connexion', null = True)
	cyber = models.ForeignKey(Cyber)
	connexions_simultanees = models.IntegerField('Nombre maximal de connexions simultanées', default = 1)
	solde = models.DecimalField(max_digits=20, decimal_places=4, default = 0.0)
	credit_reportable = models.DecimalField('Crédit maximal reporté à la fin d\'une question', max_digits=20, decimal_places=4, default = 0.0)
	credit_min = models.DecimalField('Crédit mini pour l\'utilisateur', max_digits=20, decimal_places=4, default = 0.0)
	email = models.EmailField(max_length=250)
	user = models.OneToOneField(User, editable=False)
	def __unicode__(self):
		return self.login

class PC(models.Model):
	nom = models.CharField(max_length=200)
	cout_horaire = models.DecimalField('Coût horaire', max_digits=20, decimal_places=4)
	temps_mini_facture = models.DecimalField('Durée minimum facturée (min)', max_digits=20, decimal_places=4, default = 5.0)
	identifiant = models.CharField(max_length=50)
	MAC = models.CharField(max_length=17, null=True)
	IPv4 = models.CharField(max_length=15, null=True)
	IPv6 = models.CharField(max_length=45, null=True)
	cyber = models.ForeignKey(Cyber)
	def __unicode__(self):
		return self.nom

class Vendeur(models.Model):
	mt_ventes = models.DecimalField('Cumul des ventes', max_digits=20, decimal_places=4, default=0)
	cyber = models.ForeignKey(Cyber)
	utilisateur = models.OneToOneField(Utilisateur)
	mt_ventes_tkt = models.DecimalField('Ventes sur des tickets', max_digits=20, decimal_places=4, default=0)
	def __unicode__(self):
		return self.utilisateur.login

class Vente(models.Model):
	date = models.DateTimeField(auto_now_add=True, editable=False)
	identifiant = models.CharField(max_length=50)
	monnaie = models.CharField(max_length=200)
	msg = models.CharField('Message', max_length=2000, null=True)
	montant = models.DecimalField('Montant crédité', max_digits=20, decimal_places=4)
	nv_solde_utilisateur = models.DecimalField('Nouveau solde', max_digits=20, decimal_places=4)
	vendeur = models.ForeignKey(Vendeur)
	utilisateur = models.ForeignKey(Utilisateur)
	reduction_pct = models.DecimalField('% Réduction', max_digits=4, decimal_places=2, default=0)
	reduction_motif = models.CharField('Motif réduction', max_length=200, null=True, default=None)
	montant_paye = models.DecimalField(max_digits=20, decimal_places=4)
	def __unicode__(self):
		if(msg != None):
			return msg
		else:
#			return "%s - (%s, vendu par %s)" % (date.isoformat(' '), utilisateur.nom, vendeur__nom)
			return "%s - (%s %s)" % (self.date.isoformat(' '), self.montant, self.monnaie)

class Connexion(models.Model):
	date_debut = models.DateTimeField()
	date_fin = models.DateTimeField(db_index=True)
	identifiant = models.CharField(max_length=50)
	solde_debut = models.DecimalField('Solde initial', max_digits=20, decimal_places=4)
	solde_fin = models.DecimalField('Solde final', max_digits=20, decimal_places=4)
	credit_reportable = models.DecimalField('Credit reportable', max_digits=20, decimal_places=4)
	credit_min = models.DecimalField('Crédit mini', max_digits=20, decimal_places=4)
	msg = models.CharField('Message', max_length=2000, null=True)
	utilisateur = models.ForeignKey(Utilisateur)
	PC = models.ForeignKey(PC)
	def __unicode__(self):
		return "(%s -> %s)" % (date_debut.isoformat(' '), date_fin.isoformat(' '))

class Ticket(models.Model):
	min_vendues = models.IntegerField('Nombre minutes de connexion', default = 60)
	min_conso = models.DecimalField('Nombre minutes consommées', max_digits=20, decimal_places=4, default = 0, validators=[MinValueValidator(Decimal('0.0'))] )
	min_reportables = models.IntegerField('Nombre minutes reportables (dans la limite du crédit)', default = 6000)
	mt_ventes = models.DecimalField('Montant payé', max_digits=20, decimal_places=4)
	nb_con = models.IntegerField('Nombre de connexions effectuées', default = 0)
	nb_ventes = models.IntegerField('Nombre de ventes', default = 0)
	identifiant = models.CharField(max_length=50)
	date_crea = models.DateTimeField(auto_now_add=True, editable=False)
	utilisateur = models.ForeignKey(Utilisateur, null=True)
	createur = models.ForeignKey(Vendeur)
	connexions_simultanees = models.IntegerField('Nombre maximal de connexions simultanées', default = 1)

class TicketVente(models.Model):
	min_vendues = models.IntegerField('Nombre minutes de connexion', default = 60)
	ticket = models.ForeignKey(Ticket)
	mt = models.DecimalField('Montant vendu', max_digits=20, decimal_places=4)
	date = models.DateTimeField(auto_now_add=True, editable=False)
	vendeur = models.ForeignKey(Vendeur)

class TicketConnexion(models.Model):
	min_conso = models.IntegerField('Nombre de minutes de connexion')
	ticket = models.ForeignKey(Ticket)
	minutes_init = models.IntegerField('Solde initial à la connexion')
	minutes_fin = models.IntegerField('Solde final de la connexion')
	date_debut = models.DateTimeField()
	date_fin = models.DateTimeField(db_index=True)
	PC = models.ForeignKey(PC)

class UtilisateurForm(ModelForm):
	class Meta:
		model = Utilisateur
		fields = ('login', 'identifiant', 'type_compte', 'date_naissance', 'connexions_simultanees', 'credit_reportable', 'credit_min', 'email')

class VendeurForm(ModelForm):
	class Meta:
		model = Vendeur
		fields = ('utilisateur', 'mt_ventes')

class TicketForm(ModelForm):
	class Meta:
		model = Ticket
		fields = ('utilisateur', 'mt_ventes', 'min_vendues', 'identifiant', 'min_reportables', 'connexions_simultanees')

class VenteForm(ModelForm):
	class Meta:
		model = Vente
		fields = ('vendeur', 'utilisateur', 'montant', 'reduction_pct', 'montant_paye', 'monnaie', 'reduction_motif', 'identifiant', 'msg')
		widgets = {'msg': Textarea(attrs={'cols': 60, 'rows': 3})}
