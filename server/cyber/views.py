# coding=UTF-8
# Create your views here.
from django.utils import timezone
import datetime
from datetime import timedelta
import re
import json
from django.template import Context, RequestContext
from django import http
from django.shortcuts import render_to_response, get_object_or_404
from cyber.models import User, Vendeur, VendeurForm, Utilisateur, UtilisateurForm, Vente, VenteForm, Connexion, PC, Ticket, TicketForm, TicketVente, TicketConnexion
from django.views.generic.list_detail import object_list
from django.contrib import auth
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from decimal import *
import random
#from django.contrib.auth.models import User

def newVendeur(request):
	if request.method == 'POST':
		form_v = VendeurForm(request.POST)
		if form_v.is_valid():
			if request.user != request.user.get_profile().cyber.user:
				return http.HttpResponseForbidden()
			v = Vendeur.objects.create(
				utilisateur = form_v.cleaned_data['utilisateur'],
				mt_ventes = form_v.cleaned_data['mt_ventes'],
				cyber = request.user.get_profile().cyber
			)
			return http.HttpResponseRedirect(reverse('vendeurDetail', kwargs={'pk': v.id}))
		else:
			#erreur
			form_v.fields['utilisateur'].queryset = Utilisateur.objects.filter(cyber=request.user.get_profile().cyber)
			
			template_vars = RequestContext(
				request, {
					'form': form_v,
					'utilisateur': request.user
				}
			)
			return render_to_response('cyber/vendeur_creer.html', template_vars)

	else:
		#formulaire de création
		form = VendeurForm()
		form.fields['utilisateur'].queryset = Utilisateur.objects.filter(cyber=request.user.get_profile().cyber)
		template_vars = RequestContext(request, {'form': form, 'user': request.user})
		return render_to_response('cyber/vendeur_creer.html', template_vars)

def editVendeur(request, pk):
	s = get_object_or_404(Vendeur, pk=pk)
	if request.method == 'POST':
		form_v = VendeurForm(request.POST)
		if form_v.is_valid():
			#Non autorisé si cyber <> ou user non gérant du cyber
			if s.cyber != request.user.get_profile().cyber or request.user != request.user.get_profile().cyber.user:
				return http.HttpResponseForbidden()
			s.utilisateur = form_v.cleaned_data['utilisateur']
			s.mt_ventes = form_v.cleaned_data['mt_ventes']
			s.cyber = request.user.get_profile().cyber
			s.save()
			return http.HttpResponseRedirect(reverse('vendeurDetail', kwargs={'pk':s.id}))
		else:
			form_v.fields['utilisateur'].queryset = Utilisateur.objects.filter(cyber=request.user.get_profile().cyber)
			template_vars = RequestContext(request, {'form': form_v, 'user': request.user})
			return render_to_response('cyber/vendeur_edit.html', template_vars)
	else:
		form_v = VendeurForm(instance = s)
		form_v.fields['utilisateur'].queryset = Utilisateur.objects.filter(cyber=request.user.get_profile().cyber)
		template_vars = RequestContext(request, {'form': form_v, 'user': request.user})
		return render_to_response('cyber/vendeur_edit.html', template_vars)

#	s_data = {
#		'user': s.user,
#		'nom': s.nom,
#		'prenom': s.prenom
#	}
#	form = VendeurForm(initial=s_data)
def Vendre(request):
	if request.user.get_profile().vendeur:
		if request.method == 'POST':
			form_v = VenteForm(request.POST)
			if form_v.is_valid():
				s = get_object_or_404(Vendeur, pk=form_v.cleaned_data['vendeur'].id)
				u = get_object_or_404(Utilisateur, pk=form_v.cleaned_data['utilisateur'].id)
				c_s = s.cyber
				c_u = u.cyber
				c_s_u = c_s.user.get_profile().cyber
				if c_s_u != c_u or c_s_u != c_s or c_s_u !=request.user.get_profile().cyber:
					return http.HttpResponseRedirect(reverse('listVentes'))
				if form_v.cleaned_data['reduction_pct'] <> 0.0:
					if abs(100*(form_v.cleaned_data['montant']-form_v.cleaned_data['montant_paye'])/form_v.cleaned_data['montant'] - form_v.cleaned_data['reduction_pct']) > 1:
						form_v.fields['utilisateur'].queryset = Utilisateur.objects.filter(cyber=request.user.get_profile().cyber)
						form_v.fields['vendeur'].queryset = Vendeur.objects.filter(utilisateur__cyber=request.user.get_profile().cyber)
						template_vars = RequestContext(request, {'form': form_v, 'user': request.user, 'message_erreur': 'Transaction non enregistrée, vérifiez le pourcentage de réduction!'})
						return render_to_response('cyber/vendre.html', template_vars)

				v = Vente.objects.create(
					vendeur = form_v.cleaned_data['vendeur'],
					utilisateur = form_v.cleaned_data['utilisateur'],
					montant = form_v.cleaned_data['montant'],
					monnaie = form_v.cleaned_data['monnaie'],
					identifiant = form_v.cleaned_data['identifiant'],
					msg = form_v.cleaned_data['msg'],
					nv_solde_utilisateur = u.solde + form_v.cleaned_data['montant'],
					reduction_motif = form_v.cleaned_data['reduction_motif'],
					reduction_pct = form_v.cleaned_data['reduction_pct'],
					montant_paye = form_v.cleaned_data['montant_paye'],
				)
				s.mt_ventes = s.mt_ventes + v.montant
				u.solde = u.solde + v.montant
				s.save()
				u.save()
				return http.HttpResponseRedirect(reverse('listVentes'))
			else:
				form_v.fields['utilisateur'].queryset = Utilisateur.objects.filter(cyber=request.user.get_profile().cyber)
				form_v.fields['vendeur'].queryset = Vendeur.objects.filter(utilisateur__cyber=request.user.get_profile().cyber)
				template_vars = RequestContext(request, {'form': form_v, 'user': request.user, 'message_erreur': 'Transaction non enregistrée, remplissez bien tous les champs obligatoires'})
				return render_to_response('cyber/vendre.html', template_vars)

		else:
			form_v = VenteForm({'monnaie': request.user.get_profile().cyber.monnaie
				, 'utilisateur': ''
				, 'vendeur': request.user.get_profile().vendeur.id
				, 'montant': 10
				, 'identifiant': str(datetime.datetime.now())
				, 'msg': str(datetime.datetime.now())
				, 'reduction_pct': 0
				, 'reduction_motif': 'Pas de réduction'})
			form_v.fields['utilisateur'].queryset = Utilisateur.objects.filter(cyber=request.user.get_profile().cyber)
			form_v.fields['vendeur'].queryset = Vendeur.objects.filter(utilisateur__cyber=request.user.get_profile().cyber)
			template_vars = RequestContext(request, {'form': form_v, 'user': request.user})
			return render_to_response('cyber/vendre.html', template_vars)
	else:
		return http.HttpResponseForbidden()

def newUtilisateur(request):
	if request.method == 'POST':
		form_v = UtilisateurForm(request.POST)
		if form_v.is_valid():
			#Seul le gérant peut créer des utilisateurs
			if request.user != request.user.get_profile().cyber.user:
				return http.HttpResponseForbidden()
			mdp = datetime.datetime.now()
			rx = re.compile('\W+')
			u_login = rx.sub('_', form_v.cleaned_data['login']).strip()[:30]
			u = User.objects.create_user(u_login, form_v.cleaned_data['email'], mdp)
			v = Utilisateur.objects.create(
				login = form_v.cleaned_data['login'],
				identifiant = form_v.cleaned_data['type_compte'],
				date_naissance = form_v.cleaned_data['date_naissance'],
				cyber = request.user.get_profile().cyber,
				connexions_simultanees = form_v.cleaned_data['connexions_simultanees'],
				solde = 0,
				credit_reportable = form_v.cleaned_data['credit_reportable'],
				credit_min = form_v.cleaned_data['credit_min'],
				email = form_v.cleaned_data['email'],
				user = u,
			)
			message = 'Enregistrement de %s comme utilisateur OK. Pour la connexion au site, il utilisera le login %s et le mot de passe %s. Notez les bien, le mot de passe n\'est pas enregistre tel quel' % (form_v.cleaned_data['login'], u_login, mdp)
			template_vars = RequestContext(
				request, {
					'utilisateur': v,
					'user': u,
					'message': message
				}
			)
			return render_to_response('cyber/utilisateur.html', template_vars)
		else:
			#erreur
			template_vars = RequestContext(
				request, {
					'form': form_v,
					'utilisateur': request.user,
					'message': 'Erreur lors de la création de l\'utilisateur : remplissez bien tous les champs'
				}
			)
			return render_to_response('cyber/utilisateur_creer.html', template_vars)

	else:
		#formulaire de création
		form = UtilisateurForm()
		template_vars = RequestContext(request, {'form': form, 'user': request.user})
		return render_to_response('cyber/utilisateur_creer.html', template_vars)

def saveTicket(ticket_id, ticket_form, createur):
	ticket = None
	if ticket_id is None:
		ticket = Ticket.objects.create(
			min_vendues = ticket_form.cleaned_data['min_vendues'],
			min_conso = 0,
			min_reportables = ticket_form.cleaned_data['min_reportables'],
			mt_ventes = ticket_form.cleaned_data['mt_ventes'],
			nb_con = 0,
			nb_ventes = 1,
			identifiant = ticket_form.cleaned_data['identifiant'],
			utilisateur = ticket_form.cleaned_data['utilisateur'],
			createur = createur,
			connexions_simultanees = ticket_form.cleaned_data['connexions_simultanees'])

	else:
		ticket = get_object_or_404(Ticket, pk=ticket_id)
		ticket.min_vendues += ticket_form.cleaned_data['min_vendues']
		ticket.mt_ventes += ticket_form.cleaned_data['mt_ventes']
		ticket.min_reportables = ticket_form.cleaned_data['min_reportables']
		ticket.connexions_simultanees = ticket_form.cleaned_data['connexions_simultanees']
		ticket.utilisateur = ticket_form.cleaned_data['utilisateur']
		ticket.nb_ventes += 1
		ticket.save()
	ticket_vente = TicketVente.objects.create(
		min_vendues = ticket_form.cleaned_data['min_vendues'],
		ticket = ticket,
		mt = ticket_form.cleaned_data['mt_ventes'],
		vendeur = createur
	)
	createur.mt_ventes_tkt = createur.mt_ventes_tkt+ticket_form.cleaned_data['mt_ventes']
	createur.save()
	return ticket.id

def listTickets(request, page):
	if request.method == 'POST':
		if 's' in request.POST:
			s = request.POST['s']
		else:
			template_vars = RequestContext(request)
			return render_to_response('cyber/ticket_search.html', template_vars)
#		sql = 'select t.* from cyber_ticket as t inner join cyber_utilisateur as u on u.id = t.utilisateur_id where '

		tickets = None
		if s.isnumeric():
			tickets = Ticket.objects.filter(id=int(s)).order_by('-date_crea')
#			sql += 'id = ' + s
		elif s == '*':
			tickets = Ticket.objects.all().order_by('-date_crea')
		elif len(s) < 20:
#			sql += 'identifiant like \'%' + s.replace('\'', '').replace('--', '').replace('*', '%') + '%\' or '
#			sql += 'u.login like \'%' + s.replace('\'', '').replace('--', '').replace('*', '%') + '%\' or '
#			sql += 'cast(date_crea as varchar(30)) like \'' + s.replace('\'', '').replace('--', '') + '%\';'
			tickets = Ticket.objects.filter(identifiant__icontains=s).order_by('-date_crea')
		else:
			return render_to_response('cyber/ticket_search.html')
#		tickets = Ticket.objects.raw(sql)
		template_vars = RequestContext(request, {'ticket_list': tickets})
		return object_list(request, queryset = tickets, template_name = 'cyber/ticket_search.html', paginate_by = 25, page = page, extra_context={'searched': s})#)
	else:	#formulaire
		template_vars = RequestContext(request)
		return render_to_response('cyber/ticket_search.html', template_vars)

def newTicket(request):
	if request.method == 'POST':
		ticket_form = TicketForm(request.POST)
		ticket_form.fields['utilisateur'].required = False
		if ticket_form.is_valid():
			t_id = saveTicket(None,ticket_form, request.user.get_profile().vendeur)
			return http.HttpResponseRedirect(reverse('editTicket', kwargs={'pk':t_id}))
		else:
			#erreur
			ticket_form.fields['utilisateur'].queryset = Utilisateur.objects.filter(cyber=request.user.get_profile().cyber)
			template_vars = RequestContext(
				request, {
					'form': ticket_form,
				}
			)
			return render_to_response('cyber/ticket_creer.html', template_vars)
	else:
		ticket_form = TicketForm()
		ticket_form.fields['utilisateur'].queryset = Utilisateur.objects.filter(cyber=request.user.get_profile().cyber)

		ticket_form.fields['identifiant'].value = 'T'+str(random.randint(1000000, 10000000))
		template_vars = RequestContext(
			request, {
				'form': ticket_form,
			}
		)
		return render_to_response('cyber/ticket_creer.html', template_vars)

def editTicket(request, pk):
	if request.method == 'POST':
		ticket_form = TicketForm(request.POST)
		ticket_form.fields['utilisateur'].required = False
		if ticket_form.is_valid():
			t_id = saveTicket(pk,ticket_form, request.user.get_profile().vendeur)
			return http.HttpResponseRedirect(reverse('editTicket', kwargs={'pk':t_id}))
		else:
			#erreur
			ticket_form.fields['utilisateur'].queryset = Utilisateur.objects.filter(cyber=request.user.get_profile().cyber)
			template_vars = RequestContext(
				request, {
					'ticket' : ticket
					, 'form': ticket_form,
				}
			)
			return render_to_response('cyber/ticket_edit.html', template_vars)
	else:
		ticket = get_object_or_404(Ticket, pk=pk)
		ticket_form = TicketForm(instance = ticket)
		ticket_form.fields['utilisateur'].queryset = Utilisateur.objects.filter(cyber=request.user.get_profile().cyber)
		template_vars = RequestContext(
			request, {
				'ticket' : ticket
				, 'form': ticket_form,
			}
		)
		return render_to_response('cyber/ticket_edit.html', template_vars)

def listUtilisateurs(request, page):
	if request.user != request.user.get_profile().cyber.user and request.user.get_profile().vendeur is None:
		return http.HttpResponseForbidden()
	utilisateur_list = Utilisateur.objects.filter(cyber=request.user.get_profile().cyber)
	return object_list(request, paginate_by=25, queryset=utilisateur_list, template_name='cyber/utilisateur_list.html', page=page)

def listVendeurVentes(request, vendeur_id, page):
	if request.user != request.user.get_profile().cyber.user and request.user.get_profile().vendeur.id <> vendeur_id:
		return http.HttpResponseForbidden()
	vente_list = Vente.objects.filter(vendeur=vendeur_id)
	return object_list(request, paginate_by=25, queryset=vente_list, template_name='cyber/vente_list.html', page=page, extra_context={'vendeur_id': vendeur_id})

def listVendeurVentesTkt(request, vendeur_id, page):
	if request.user != request.user.get_profile().cyber.user:	#le gérant
		if request.user.get_profile().vendeur.id <> vendeur_id:	#Le vendeur en question
			return http.HttpResponseForbidden()
	vente_list = TicketVente.objects.filter(vendeur=vendeur_id).order_by('-date')
	return object_list(request, paginate_by=25, queryset=vente_list, template_name='cyber/vente_tkt_list.html', page=page, extra_context={'vendeur_id': vendeur_id})

def listUtilisateurConnexions(request, utilisateur_id, page):
	if request.user != request.user.get_profile().cyber.user and request.user.get_profile().id <> utilisateur_id:
		return http.HttpResponseForbidden()
	u = get_object_or_404(Utilisateur, pk=utilisateur_id)
	conn_list = u.connexion_set.all()
	return object_list(request, paginate_by=25, queryset=conn_list, template_name='cyber/conn_list.html', page=page)

def listUtilisateurTkt(request, utilisateur_id, page):
	if request.user != request.user.get_profile().cyber.user and request.user.get_profile().id <> utilisateur_id:
		return http.HttpResponseForbidden()
	u = get_object_or_404(Utilisateur, pk=utilisateur_id)
	conn_list = u.ticket_set.all()
	return object_list(request, paginate_by=25, queryset=conn_list, template_name='cyber/tkt_list.html', page=page, extra_context={'utilisateur_id': utilisateur_id})

def listVentes(request, page):
	if request.user.is_active == 0 or request.user.get_profile() is None or request.user is None:
		return http.HttpResponseForbidden()
#	request.user != request.user.get_profile().cyber.user and request.user.get_profile().vendeur is None and
	vente_list = None
	if request.user == request.user.get_profile().cyber.user:	#le gérant
		vente_list = Vente.objects.order_by('-date')
	else:
		if request.user.get_profile().vendeur is not None:
			vente_list = Vente.objects.filter(vendeur=request.user.get_profile().vendeur).order_by('-date')
		else:
			vente_list = Vente.objects.filter(utilisateur=request.user.get_profile()).order_by('-date')
	return object_list(request, paginate_by=25, queryset=vente_list, template_name='cyber/vente_list.html', page=page)

def listVentesTkt(request, ticket_id, page):
	if request.user.is_active == 0 or request.user.get_profile() is None or request.user is None:
		return http.HttpResponseForbidden()
#	request.user != request.user.get_profile().cyber.user and request.user.get_profile().vendeur is None and
	t = get_object_or_404(Ticket, pk=ticket_id)
	vente_list = None
	if request.user == request.user.get_profile().cyber.user:	#le gérant
		vente_list = t.ticketvente_set.order_by('-date')
	else:
		if request.user.get_profile().vendeur is not None:
			vente_list = t.ticketvente_set.filter(vendeur=request.user.get_profile().vendeur).order_by('-date')
		else:
			if t.utilisateur == request.user.get_profile():
				vente_list = t.ticketvente_set.filter(utilisateur=request.user.get_profile()).order_by('-date')
	return object_list(request, paginate_by=25, queryset=vente_list, template_name='cyber/vente_tkt_list.html', page=page, extra_context={'ticket_id': ticket_id})

def listTktVentes(request, page):
	if request.user.is_active == 0 or request.user.get_profile() is None or request.user is None:
		return http.HttpResponseForbidden()
#	request.user != request.user.get_profile().cyber.user and request.user.get_profile().vendeur is None and
	vente_list = None
	if request.user == request.user.get_profile().cyber.user:	#le gérant
		vente_list = TicketVente.objects.order_by('-date')
	else:
		if request.user.get_profile().vendeur is not None:
			vente_list = TicketVente.objects.filter(vendeur=request.user.get_profile().vendeur).order_by('-date')
		else:
			if t.utilisateur == request.user.get_profile():
				vente_list = TicketVente.objects.filter(utilisateur=request.user.get_profile()).order_by('-date')
	return object_list(request, paginate_by=25, queryset=vente_list, template_name='cyber/vente_tkt_list.html', page=page)

def listSessions(request, page):
	if request.user.is_active == 0 or request.user.get_profile() is None or request.user is None:
		return http.HttpResponseForbidden()
#	request.user != request.user.get_profile().cyber.user and request.user.get_profile().vendeur is None and
	session_list = Connexion.objects.order_by('-date_debut')#None
#	if request.user == request.user.get_profile().cyber.user:	#le gérant
#		session_list = Connexion.objects.order_by('-date')
#	else:
#		if request.user.get_profile().vendeur is not None:
#			session_list = Connexion.objects.order_by('-date')
#		else:
#			session_list = Connexion.objects.filter(utilisateur=request.user.get_profile()).order_by('-date')
	return object_list(request, paginate_by=25, queryset=session_list, template_name='cyber/session_list.html', page=page)

def listTktSessions(request, page):
	if request.user.is_active == 0 or request.user.get_profile() is None or request.user is None:
		return http.HttpResponseForbidden()
#	request.user != request.user.get_profile().cyber.user and request.user.get_profile().vendeur is None and
#	session_list = TicketConnexion.objects.order_by('-date_debut')#None
	if request.user == request.user.get_profile().cyber.user:	#le gérant
		session_list = TicketConnexion.objects.order_by('-date_debut')
	else:
		if request.user.get_profile().vendeur is not None:
			session_list = TicketConnexion.objects.filter(ticket__createur=request.user.get_profile()).order_by('-date_debut')
		else:
			session_list = TicketConnexion.objects.filter(ticket__utilisateur=request.user.get_profile()).order_by('-date_debut')
	return object_list(request, paginate_by=25, queryset=session_list, template_name='cyber/session_tkt_list.html', page=page)

def listSessionsTkt(request, ticket_id, page):
	if request.user.is_active == 0 or request.user.get_profile() is None or request.user is None:
		return http.HttpResponseForbidden()
#	request.user != request.user.get_profile().cyber.user and request.user.get_profile().vendeur is None and
#	session_list = TicketConnexion.objects.order_by('-date_debut')#None
	u = get_object_or_404(Ticket, pk=ticket_id)
	if request.user == request.user.get_profile().cyber.user:	#le gérant
		session_list = u.ticketconnexion_set.order_by('-date_debut')
	else:
		if request.user.get_profile().vendeur is not None:	#juste un vendeur : il peut voir ses tickets
			if u.createur == request.user.get_profile().vendeur:
				session_list = u.ticketconnexion_set.order_by('-date_debut')
			else:
				return http.HttpResponseForbidden()#ticket d'un autre vendeur
		else:
			if request.user.get_profile() is not None:	#juste un vendeur : il peut voir ses tickets
				if u.utilisateur == request.user.get_profile():
					session_list = u.ticketconnexion_set.order_by('-date_debut')
				else:
					return http.HttpResponseForbidden()#ticket d'un autre vendeur
				session_list = u.ticketconnexion_set.order_by('-date_debut')
			else:
				return http.HttpResponseForbidden()#ticket d'un autre utilisateur
	return object_list(request, paginate_by=25, queryset=session_list, template_name='cyber/session_tkt_list.html', page=page, extra_context={'ticket_id': ticket_id})

def accueil(request):
	template_vars = RequestContext(
		request, {
			'utilisateur': request.user
		})
	return render_to_response('cyber/accueil.html', template_vars)

def logout(request):
	login = ''
	mdp = ''
	message = 'Vous avez été déconnecté, à bientôt. Vous pouvez maintenant vous reconnecter avec un autre compte.'
	auth.logout(request)
	template_vars = RequestContext(
	request, {
		'login': login,
		'message': message,
		'mdp': mdp
	})
	return render_to_response('cyber/login.html', template_vars)

def login(request):
	if request.method == 'POST':
		username = request.POST['login']
		mdp = request.POST['mdp']
		user = auth.authenticate(username=username, password=mdp)
		if user is not None:
			if user.is_active:
				auth.login(request, user)
				return http.HttpResponseRedirect(reverse('accueil'))
			else:
				message = 'Votre compte est désactivé'
				template_vars = RequestContext(
				request, {
					'login': username,
					'message': message,
					'mdp': mdp
				}
				)
				return render_to_response('cyber/login.html', template_vars)
		else:
			message = 'Connexion impossible : Utilisateur ou mot de passe incorrect'
			template_vars = RequestContext(
			request, {
				'login': username,
				'message': message,
				'mdp': mdp
			})
			return render_to_response('cyber/login.html', template_vars)
	else:
		login = ''
		mdp = ''
		message = ''
		template_vars = RequestContext(
		request, {
			'login': login,
			'message': message,
			'mdp': mdp
		})
		return render_to_response('cyber/login.html', template_vars)

@csrf_exempt
def ticket_session_start(request):
	erreur=0
	message=''
	cpt_sessions = 0
	response_data={}
	if request.method == 'POST':
		donnees = request.POST['donnees']
		if donnees is not None:
			infos = json.loads(donnees)
			PC_id = int(infos['PC_id'])
			PC_identifiant = infos['PC_identifiant']
			pc = get_object_or_404(PC, pk=PC_id)
			ticket_id = int(infos['ticket_id'])
			ticket_identifiant = infos['ticket_identifiant']

			ticket = get_object_or_404(Ticket, pk=ticket_id)
			if ticket.identifiant != ticket_identifiant:
				erreur = 403
				message = 'Ticket non identifié, N° de ticket ou identifiant errone'
			else:
				if ticket.utilisateur is not None:	#Si on a un utilisateur affecté au ticket, on vérifie que le login correspond
					if 'login' in infos:
						login = infos['login']
						if ticket.utilisateur.login != login:
							erreur = 403
							message = 'Le ticket n\'appartient pas au bon utilisateur'
					else:
						erreur = 403
						message = 'Le ticket a un utilisateur mais pas la requete de connexion. Attendu "login":"LOGIN"'
	
			sessions_en_cours = TicketConnexion.objects.filter(ticket=ticket, date_fin__gte = timezone.now())
			connexions = []
			for session in sessions_en_cours:
				c_pc = session.PC
				connexions.append( {'courante':0,'date_debut':str(session.date_debut),'date_fin':str(session.date_fin), 'min_conso':str(session.min_conso) 
					, 'ticket':{'id': session.ticket.id, 'identifiant':session.ticket.identifiant }
					, 'minutes_init':session.minutes_init , 'minutes_fin':session.minutes_fin ,
				'pc':{'id':c_pc.id,'identifiant':c_pc.identifiant,'temps_mini_facture':str(c_pc.temps_mini_facture),'cout_horaire':str(c_pc.cout_horaire)},
				})
				cpt_sessions = cpt_sessions+1
			if cpt_sessions >= ticket.connexions_simultanees:
				erreur = 401
				message = 'Trop de connexion(s) deja ouvertes'
				response_data['code']=erreur
				response_data['message']=message
			if ticket.min_vendues - ticket.min_conso < pc.temps_mini_facture:
				erreur = 402
				message = 'Credit insuffisant'
				response_data['code']=erreur
				response_data['message']=message
			if erreur != 0:
				response_data['code']=erreur
				response_data['message']=message
				print response_data
				return http.HttpResponseForbidden(json.dumps(response_data), mimetype="application/json")

			heure_debut = timezone.now()
			session = TicketConnexion.objects.create(
				date_debut=heure_debut
				, date_fin=heure_debut+timedelta(minutes=int(pc.temps_mini_facture))
				, minutes_init=ticket.min_vendues - ticket.min_conso
				, minutes_fin=ticket.min_vendues - ticket.min_conso-pc.temps_mini_facture
				, PC=pc
				, min_conso = int(pc.temps_mini_facture)
				, ticket = ticket
			)

			ticket.nb_con += 1
			ticket.min_conso += pc.temps_mini_facture
			ticket.save()
			connexions.append ({'courante':1, 'id': session.id,'date_debut':str(session.date_debut),'date_fin':str(session.date_fin), 'min_conso':str(session.min_conso)
				, 'ticket':{'id': session.ticket.id, 'identifiant':session.ticket.identifiant }
				, 'minutes_init':str(session.minutes_init) , 'minutes_fin':str(session.minutes_fin) ,
				'pc':{'id':pc.id,'identifiant':pc.identifiant,'temps_mini_facture':str(pc.temps_mini_facture),'cout_horaire':str(pc.cout_horaire)},
			})
			reponse = {'code':200,'message':'OK','temps_restant':str(pc.temps_mini_facture)
				,'nouveau_solde':str(ticket.min_vendues - ticket.min_conso)
				,'minutes_total_restantes':str(((session.date_fin - timezone.now()).seconds/Decimal(60))+ticket.min_vendues - ticket.min_conso)
				,'connexions':connexions
			}
#			return http.HttpResponse(str(reponse))
			return http.HttpResponse(json.dumps(reponse), mimetype="application/json")
		else:
			erreur = 400
			message = 'Requete mal formee'
			response_data['code']=erreur
			response_data['message']=message
			return http.HttpResponseBadRequest(json.dumps(response_data), mimetype="application/json")
	else:
		erreur = 400
		message = '<html><head><title>Requete mal formee</title></head><body><form method="post"><textarea name="donnees"></textarea><input type="submit"/></form></body></html>'
		response_data['code']=erreur
		response_data['message']=message
		return http.HttpResponseBadRequest(message)
		return http.HttpResponseBadRequest(json.dumps(response_data), mimetype="application/json")

@csrf_exempt
def ticket_session_close(request):
	erreur=0
	message=''
	cpt_sessions = 0
	response_data={}
	temps_restant = Decimal(0)
	temps_total_restant = 0
	heure_courante = timezone.now()
	minutes_consommees = Decimal(0)
	session_courante = None
	if request.method == 'POST':
		donnees = request.POST['donnees']
		if donnees is not None:
			infos = json.loads(donnees)
			PC_id = int(infos['PC_id'])
			PC_identifiant = infos['PC_identifiant']
			pc = get_object_or_404(PC, pk=PC_id)
			ticket_id = int(infos['ticket_id'])
			ticket_identifiant = infos['ticket_identifiant']
			session_id = infos['session_id']
			ticket = get_object_or_404(Ticket, pk=ticket_id)
			if ticket.identifiant != ticket_identifiant:
				erreur = 403
				message = 'Ticket non identifié, N° de ticket ou identifiant erroné'
			else:
				if ticket.utilisateur is not None:	#Si on a un utilisateur affecté au ticket, on vérifie que le login correspond
					if 'login' in infos:
						login = infos['login']
						if ticket.utilisateur.login != login:
							erreur = 403
							message = 'Le ticket n\'appartient pas au bon utilisateur'
					else:
						erreur = 403
						message = 'Le ticket a un utilisateur mais pas la requête de connexion. Attendu "login":"LOGIN"'
			sessions_en_cours = TicketConnexion.objects.filter(ticket=ticket, date_fin__gte = heure_courante)
			connexions = []
			trouve=0
			for session in sessions_en_cours:
				c_pc = session.PC
				if session.id == session_id:
					courante=1
					trouve=1
					session_courante = session
				else:
					courante=0
				connexions.append({'id': session.id, 'courante':courante,'date_debut':str(session.date_debut),'date_fin':str(session.date_fin), 'min_conso':str(session.min_conso)
					, 'ticket':{'id': session.ticket.id, 'identifiant':session.ticket.identifiant }
					, 'minutes_init':str(session.minutes_init) , 'minutes_fin':str(session.minutes_fin) ,
				'pc':{'id':c_pc.id,'identifiant':c_pc.identifiant,'temps_mini_facture':str(c_pc.temps_mini_facture),'cout_horaire':str(c_pc.cout_horaire)},
				})
				cpt_sessions = cpt_sessions+1
			if trouve == 0:
				erreur = 401
				message = 'Connexion non trouvée parmi les connexions ouvertes'
				response_data['code']=erreur
				response_data['message']=message
			if erreur != 0:
				response_data['code']=erreur
				response_data['message']=message
				print response_data
				return http.HttpResponseForbidden(json.dumps(response_data), mimetype="application/json")
			if session_courante.date_fin + timedelta(minutes=int(pc.temps_mini_facture)) < heure_courante:
				erreur=402
				message='Session non mise à jour depuis trop longtemps'

			heure_fin = heure_courante# + datetime.interval(minutes = pc.temps_mini_facture)
			temps_restant = 0
			temps_total_restant = 0
			ticket.min_conso -= ((session_courante.date_fin - heure_fin).seconds)/Decimal(60)
			session_courante.date_fin = heure_fin
			session_courante.minutes_fin = ticket.min_vendues - ticket.min_conso
			session_courante.save()
			ticket.save()
			reponse = {'code':200,'message':'OK','temps_restant':str(temps_restant)
				,'nouveau_solde':str(session_courante.minutes_fin)
				,'minutes_total_restantes':temps_total_restant
				,'connexions':connexions
			}
			return http.HttpResponse(json.dumps(reponse), mimetype="application/json")
		else:
			erreur = 400
			message = 'Requête mal formée'
			response_data['code']=erreur
			response_data['message']=message
			return http.HttpResponseBadRequest(json.dumps(response_data), mimetype="application/json")
	else:
		erreur = 400
		message = '<html><head><title>Requête mal formée</title></head><body><form method="post"><textarea name="donnees"></textarea><input type="submit"/></form></body></html>'
		response_data['code']=erreur
		response_data['message']=message
		return http.HttpResponseBadRequest(message)
		return http.HttpResponseBadRequest(json.dumps(response_data), mimetype="application/json")

#{"PC_id":1,"PC_identifiant": "11", "ticket_id": 1, "ticket_identifiant": "4B18UM68"}
@csrf_exempt
def ticket_session_continue(request):
	erreur=0
	message=''
	cpt_sessions = 0
	response_data={}
	temps_restant = Decimal(0)
	temps_total_restant = 0
	heure_courante = timezone.now()#datetime.datetime.now()
	minutes_consommees = Decimal(0)
	session_courante = None
	if request.method == 'POST':
		donnees = request.POST['donnees']
		if donnees is not None:
			infos = json.loads(donnees)
			PC_id = int(infos['PC_id'])
			PC_identifiant = infos['PC_identifiant']
			pc = get_object_or_404(PC, pk=PC_id)
			ticket_id = int(infos['ticket_id'])
			ticket_identifiant = infos['ticket_identifiant']
			session_id = infos['session_id']
			ticket = get_object_or_404(Ticket, pk=ticket_id)
			if ticket.identifiant != ticket_identifiant:
				erreur = 403
				message = 'Ticket non identifié, N° de ticket ou identifiant erroné'
			else:
				if ticket.utilisateur is not None:	#Si on a un utilisateur affecté au ticket, on vérifie que le login correspond
					if 'login' in infos:
						login = infos['login']
						if ticket.utilisateur.login != login:
							erreur = 403
							message = 'Le ticket n\'appartient pas au bon utilisateur'
					else:
						erreur = 403
						message = 'Le ticket a un utilisateur mais pas la requête de connexion. Attendu "login":"LOGIN"'
			#On va charcher parmi toutes les sessions en cours sur ce ticket : il faut retrouver la connexion parmi celles ouvertes. Il ne doit pas y avoir plus de connexions ouvertes que le maxi déclaré sur le ticket
			sessions_en_cours = TicketConnexion.objects.filter(ticket=ticket, date_fin__gte = heure_courante)
			connexions = []
			trouve=0
			for session in sessions_en_cours:
				c_pc = session.PC
				if session.id == int(session_id):
					courante=1
					trouve=1
					session_courante = session
				else:
					courante=0
				connexions.append({'id': session.id, 'courante':courante,'date_debut':str(session.date_debut),'date_fin':str(session.date_fin), 'min_conso':str(session.min_conso)
					, 'ticket':{'id': session.ticket.id, 'identifiant':session.ticket.identifiant }
					, 'minutes_init':session.minutes_init , 'minutes_fin':session.minutes_fin ,
				'pc':{'id':c_pc.id,'identifiant':c_pc.identifiant,'temps_mini_facture':str(c_pc.temps_mini_facture),'cout_horaire':str(c_pc.cout_horaire)},
				})
				cpt_sessions = cpt_sessions+1
			if trouve == 0:
				erreur = 401
				message = 'Connexion non trouvée parmi les connexions ouvertes'
				response_data['code']=erreur
				response_data['message']=message+str(connexions)
			if erreur != 0:
				response_data['code']=erreur
				response_data['message']=message
				print response_data
				return http.HttpResponseForbidden(json.dumps(response_data), mimetype="application/json")
			if session_courante.date_fin + timedelta(minutes=int(pc.temps_mini_facture)) < heure_courante:
				erreur=402
				message='Session non mise à jour depuis trop longtemps'
			#On compare les minutes restantes dans le solde + minutes restantes entre l'heure et la fin de session précédemment positionnée
			if (session_courante.date_fin - heure_courante).seconds/Decimal(60) + (ticket.min_vendues - ticket.min_conso) < Decimal(pc.temps_mini_facture):	#On ne peut pas soustraire temps_mini_facture
				if ticket.min_vendues <= ticket.min_conso:	#On ne peut rien soustraire
					erreur = 402
					message = 'Crédit épuisé'
					response_data['code']=erreur
					response_data['message']=message
					return http.HttpResponseForbidden(json.dumps(response_data), mimetype="application/json")
				else:	#On consomme tout ce qu'il reste
					a_ajouter = 60*(ticket.min_vendues - ticket.min_conso)
					#a_ajouter = a_ajouter+(session_courante.date_fin - heure_courante).seconds
					heure_fin = session_courante.date_fin+timedelta(seconds=int(a_ajouter))#À compléter
					temps_restant = Decimal(0)+(heure_fin - heure_courante).seconds/Decimal(60)#heure_fin-heure_courante
					temps_total_restant = temps_restant
					ticket.min_conso = ticket.min_vendues
			else:
				heure_fin = heure_courante + timedelta(minutes = int(pc.temps_mini_facture))
				temps_restant = pc.temps_mini_facture
				temps_total_restant = ticket.min_vendues - ticket.min_conso+((session_courante.date_fin-heure_courante).seconds/Decimal(60))
				ticket.min_conso += ((heure_fin - session_courante.date_fin).seconds)/Decimal(60)
			session_courante.date_fin = heure_fin
			session_courante.minutes_fin = ticket.min_vendues - ticket.min_conso
			ticket.save()
			session_courante.save()
			reponse = {'code':200,'message':'OK, heure_fin='+str(session_courante.date_fin),'temps_restant':str(temps_restant)
				,'nouveau_solde':str(session_courante.minutes_fin)
				,'minutes_total_restantes':str(temps_total_restant)
				,'connexions':connexions
			}
			return http.HttpResponse(json.dumps(reponse), mimetype="application/json")
		else:
			erreur = 400
			message = 'Requête mal formée'
			response_data['code']=erreur
			response_data['message']=message
			return http.HttpResponseBadRequest(json.dumps(response_data), mimetype="application/json")
	else:
		erreur = 400
		message = '<html><head><title>Requête mal formée</title></head><body><form method="post"><textarea name="donnees"></textarea><input type="submit"/></form></body></html>'
		response_data['code']=erreur
		response_data['message']=message
		return http.HttpResponseBadRequest(message)
		return http.HttpResponseBadRequest(json.dumps(response_data), mimetype="application/json")

@csrf_exempt
def session_start(request):
	erreur=0
	message=''
	cpt_sessions = 0
	response_data={}
	if request.method == 'POST':
		donnees = request.POST['donnees']
		if donnees is not None:
			infos = json.loads(donnees)
			PC_id = int(infos['PC_id'])
			user_id = int(infos['user_id'])
			mdp = infos['mdp']
			login = infos['login']
			user_identifiant = infos['user_identifiant']
			PC_identifiant = infos['PC_identifiant']
			pc = get_object_or_404(PC, pk=PC_id)
			user = auth.authenticate(username=login, password=mdp)#get_object_or_404(User, pk=user_id)
#			utilisateur = get_object_or_404(PC, pk=user_id)
			if user is None:
				erreur = 403
				response_data['code']=erreur
				response_data['message']=message
				message = 'Utilisateur inconnu ou problème de mot de passe'
				return http.HttpResponse(json.dumps(response_data), mimetype="application/json")	#Forbidden
			if not user.is_active:
				erreur = 403
				message = 'Utilisateur désactivé'
			if user.get_profile() is None:
				erreur = 403
				message = 'Utilisateur non connu'
			user = user.get_profile()
			if pc.cyber != user.cyber:
				erreur = 403
				message = 'Cybercafé incohérent entre l\'ordinateur et l\'utilisateur'
			if pc.identifiant != PC_identifiant or PC_id != pc.id:
				erreur = 403
				message = 'Mauvais identifiant d\'ordinateur'
			if user.identifiant != user_identifiant or user.id != user_id:
				erreur = 403
				message = 'Mauvais identifiant d\'utilisateur'
			if erreur != 0:
				response_data['code']=erreur
				response_data['message']=message
				print response_data
				return http.HttpResponse(json.dumps(response_data), mimetype="application/json")	#Forbidden

			sessions_en_cours = Connexion.objects.filter(utilisateur=user, date_fin__lte = datetime.datetime.now())
			connexions = []
			for session in sessions_en_cours:
				c_pc = session.PC
				c_user = session.utilisateur
				connexions[cpt_sessions] = {'courante':0,'date_debut':str(session.date_debut),'date_fin':str(session.date_fin),'identifiant':session.identifiant,'solde_debut':session.solde_debut,'solde_fin':session.solde_fin,'credit_reportable':session.credit_reportable,'credit_min':session.credit_min,'msg':session.msg,
				'pc':{'id':c_pc.id,'identifiant':c_pc.identifiant,'temps_mini_facture':str(c_pc.temps_mini_facture),'cout_horaire':str(c_pc.cout_horaire)},
				'utilisateur':{'connexions_simultanees':c_user.connexions_simultanees,'login':c_user.login,'id':c_user.id,'identifiant':c_user.identifiant,'credit_min':c_user.credit_min,'solde':c_user.solde,'credit_reportable':c_user.credit_reportable,'type_compte':c_user.type_compte},
				}
				cpt_sessions = cpt_sessions+1
			if cpt_sessions >= user.connexions_simultanees:
				erreur = 401
				message = 'Trop de connexion(s) déjà ouvertes'
				response_data['code']=erreur
				response_data['message']=message
				return http.HttpResponse(json.dumps(response_data), mimetype="application/json")	#Forbidden

			cout = pc.temps_mini_facture * pc.cout_horaire/Decimal(60)
			if user.solde - cout < user.credit_min:
				erreur = 402
				message = 'Crédit insuffisant'
				response_data['code']=erreur
				response_data['message']=message
				return http.HttpResponse(json.dumps(response_data), mimetype="application/json")#Forbidden

			heure_debut = datetime.datetime.now()
			session = Connexion.objects.create(
				date_debut=heure_debut
				, date_fin=heure_debut+timedelta(minutes=int(pc.temps_mini_facture))
				, identifiant=str(heure_debut)
				, solde_debut=user.solde
				, solde_fin=user.solde-cout
				, credit_reportable=user.credit_reportable
				, credit_min=user.credit_min
				, msg='Connexion ouverte - %s, solde = %s' % (str(datetime.datetime.now()), str(user.solde-cout))
				, utilisateur=user
				, PC=pc
			)

			user.solde = session.solde_fin
			user.save()
			connexions.append ({'courante':1,'date_debut':str(session.date_debut),'date_fin':str(session.date_fin),'identifiant':session.identifiant,'solde_debut':str(session.solde_debut),'solde_fin':str(session.solde_fin),'credit_reportable':str(session.credit_reportable),'credit_min':str(session.credit_min),'msg':session.msg,
			'pc':{'id':pc.id,'identifiant':pc.identifiant,'temps_mini_facture':str(pc.temps_mini_facture),'cout_horaire':str(pc.cout_horaire)},
			'utilisateur':{'connexions_simultanees':user.connexions_simultanees,'login':user.login,'id':user.id,'identifiant':user.identifiant,'credit_min':str(user.credit_min),'solde':str(user.solde),'credit_reportable':str(user.credit_reportable),'type_compte':user.type_compte},
			})

			reponse = {'code':200,'message':'OK','temps_restant':str(pc.temps_mini_facture)
				,'nouveau_solde':str(session.solde_fin)
				,'minutes_total_restantes':str(Decimal(60)*user.solde/pc.cout_horaire)
				,'connexions':connexions
			}
			return http.HttpResponse(json.dumps(reponse), mimetype="application/json")
		else:
			erreur = 400
			message = 'Requête mal formée'
			response_data['code']=erreur
			response_data['message']=message
			return http.HttpResponseBadRequest(json.dumps(response_data), mimetype="application/json")
	else:
		erreur = 400
		message = '<html><head><title>Requête mal formée</title></head><body><form method="post"><textarea name="donnees"></textarea><input type="submit"/></form></body></html>'
		response_data['code']=erreur
		response_data['message']=message
#		return http.HttpResponseBadRequest(message)
		return http.HttpResponseBadRequest(json.dumps(response_data), mimetype="application/json")

@csrf_exempt
def session_continue(request):
	erreur=0
	message=''
	cpt_sessions = 0
	response_data={}
	if request.method == 'POST':
		donnees = request.POST['donnees']
		if donnees is not None:
			infos = json.loads(donnees)
			PC_id = infos['PC_id']
			user_id = infos['user_id']
			mdp = infos['mdp']
			login = infos['login']
			user_identifiant = infos['user_identifiant']
			PC_identifiant = infos['PC_identifiant']
			pc = get_object_or_404(PC, pk=PC_id)
#			identifiant = infos['connexion_id']
			session_id = int(infos['session_id'])

			session = get_object_or_404(Connexion, pk=session_id)
			pc = get_object_or_404(PC, pk=PC_id)
			user = auth.authenticate(username=login, password=mdp)#get_object_or_404(User, pk=user_id)
			if user is None:
				erreur = 403
				response_data['code']=erreur
				response_data['message']=message
				message = 'Utilisateur inconnu ou problème de mot de passe'
				return http.HttpResponseForbidden(json.dumps(response_data), mimetype="application/json")
			if not user.is_active:
				erreur = 403
				message = 'Utilisateur désactivé'
			if user.get_profile() is None:
				erreur = 403
				message = 'Utilisateur non connu'
			user = user.get_profile()
			if pc.cyber != user.cyber:
				erreur = 403
				message = 'Cybercafé incohérent entre l\'ordinateur et l\'utilisateur'
			if pc.identifiant != PC_identifiant or PC_id != pc.id or session.PC != pc:
				erreur = 403
				message = 'Mauvais identifiant d\'ordinateur'
			if user.identifiant != user_identifiant or user.id != user_id or session.utilisateur != user:
				erreur = 403
				message = 'Mauvais identifiant d\'utilisateur'
			if erreur != 0:
				response_data['code']=erreur
				response_data['message']=message
				return http.HttpResponseForbidden(json.dumps(response_data), mimetype="application/json")

			sessions_en_cours = Connexion.objects.filter(utilisateur=c_user,date_fin__lte=datetime.datetime.now())
			trouve=0
			heure_courante = datetime.datetime.now()
			heure_fin = heure_courante+date.interval(minutes=int(pc.temps_mini_facture))
			connexions = []
			for sessions in sessions_en_cours:
				c_pc = sessions.PC
				c_user = sessions.utilisateur
				if session.id == sessions.id:
					courante=1
					trouve=1
					if session.date_fin + timedelta(minutes=int(pc.temps_mini_facture)) < heure_courante:
						erreur=402
						message='Session non mise à jour depuis trop longtemps'
				else:
					courante=0
				connexions[cpt_sessions] = {'courante':courante,'date_debut':sessions.date_debut,'date_fin':sessions.date_fin,'identifiant':sessions.identifiant,'solde_debut':str(sessions.solde_debut),'solde_fin':str(sessions.solde_fin),'credit_reportable':str(sessions.credit_reportable),'credit_min':str(sessions.credit_min),'msg':sessions.msg,
				'pc':{'id':c_pc.id,'identifiant':c_pc.identifiant,'temps_mini_facture':str(c_pc.temps_mini_facture),'cout_horaire':str(c_pc.cout_horaire)},
				'utilisateur':{'connexions_simultanees':c_user.connexions_simultanees,'login':c_user.login,'id':c_user.id,'identifiant':c_user.identifiant,'credit_min':str(c_user.credit_min),'solde':str(c_user.solde),'credit_reportable':str(c_user.credit_reportable),'type_compte':c_user.type_compte},
				}
				cpt_sessions = cpt_sessions+1
			if trouve == 0:
				erreur = 402
				message = 'Session introuvable'
			if erreur > 0:
				response_data['code']=erreur
				response_data['message']=message
				return http.HttpResponseNotFound(json.dumps(response_data), mimetype="application/json")
			cout = (heure_fin - session.date_fin).minutes * pc.cout_horaire/Decimal(60)
			if user.solde - cout < user.credit_min:
				erreur = 402
				message = 'Crédit insuffisant'
				response_data['code']=erreur
				response_data['message']=message
				return http.HttpResponseForbidden(json.dumps(response_data), mimetype="application/json")

			session.date_fin=heure_fin
			session.solde_fin=user.solde-cout
			session.msg= session.msg + 'Connexion continuée- %s, solde = %s' % (str(datetime.datetime.now()), str(session.solde_fin))

			session.save
			user.solde = session.solde_fin
			user.save()

			reponse = {'code':200,'message':'OK','temps_restant':str(pc.temps_mini_facture)
				,'nouveau_solde':session.solde_fin
				,'minutes_total_restantes':str(Decimal(60)*user.solde/pc.cout_horaire)
				,'connexions':connexions
			}
			return http.HttpResponse(json.dumps(reponse), mimetype="application/json")
		else:
			erreur = 400
			message = 'Requête mal formée'
			response_data['code']=erreur
			response_data['message']=message
			return http.HttpResponseBadRequest(json.dumps(response_data), mimetype="application/json")
	else:
		erreur = 400
		message = 'Requête mal formée'
		response_data['code']=erreur
		response_data['message']=message
		return http.HttpResponseBadRequest(json.dumps(response_data), mimetype="application/json")

