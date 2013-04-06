from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from cyber.models import Vendeur, Utilisateur
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'phpcafe.views.home', name='home'),
    # url(r'^phpcafe/', include('phpcafe.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
	url(r'^$', 'cyber.views.accueil', name='accueil'),
	url(r'^admin/', include(admin.site.urls)),
	url(r'^login$', 'cyber.views.login', name='login'),
	url(r'^logout$', 'cyber.views.logout', name='logout'),
	url(r'^session_start$', 'cyber.views.session_start'),
	url(r'^session_continue$', 'cyber.views.session_continue'),
	url(r'^sessions/(page(?P<page>[0-9]+)/)?$', 'cyber.views.listSessions', name='listSessions'),
	url(r'^ticket/creer$', 'cyber.views.newTicket', name='newTicket'),
	url(r'^ticket/chercher/(page(?P<page>[0-9]+)/)?$', 'cyber.views.listTickets', name='listTickets'),
	url(r'^ticket/(?P<pk>\d+)/edit', 'cyber.views.editTicket', name='editTicket'),
	url(r'^ticket/session_start$', 'cyber.views.ticket_session_start'),
	url(r'^ticket/session_continue$', 'cyber.views.ticket_session_continue'),
	url(r'^ticket/session_close$', 'cyber.views.ticket_session_close'),
	url(r'^ticket/(?P<ticket_id>\d+)/sessions/(page(?P<page>[0-9]+)/)?$', 'cyber.views.listSessionsTkt', name='listSessionsTkt'),
	url(r'^ticket/(?P<ticket_id>\d+)/ventes/(page(?P<page>[0-9]+)/)?$', 'cyber.views.listVentesTkt', name='listVentesTkt'),
	url(r'^ticket/ventes/(page(?P<page>[0-9]+)/)?$', 'cyber.views.listTktVentes', name='listTktVentes'),
	url(r'^tickets/sessions/(page(?P<page>[0-9]+)/)?$', 'cyber.views.listTktSessions', name='listTktSessions'),
	url(r'^utilisateur/creer$', 'cyber.views.newUtilisateur', name='newUtilisateur'),
#	url(r'^utilisateur/(?P<pk>\d+)/modifier$', 'cyber.views.editUtilisateur'),
	url(r'^utilisateur/(?P<pk>\d+)$', DetailView.as_view(model=Utilisateur,
						template_name='cyber/utilisateur.html'), name='utilisateurList'),
	url(r'^utilisateurs/(page(?P<page>[0-9]+)/)?$', 'cyber.views.listUtilisateurs', name='listUtilisateurs'),
	url(r'^utilisateurs/(?P<utilisateur_id>\d+)/tickets/(page(?P<page>[0-9]+)/)?$', 'cyber.views.listUtilisateurTkt', name='listUtilisateurTkt'),
	url(r'^ventes/(page(?P<page>[0-9]+)/)?$', 'cyber.views.listVentes', name='listVentes'),
	url(r'^vendeurs/$', ListView.as_view(model=Vendeur, queryset=Vendeur.objects.order_by('-id'),
						template_name='cyber/vendeur_list.html'), name='vendeurList'),
	url(r'^vendeur/(?P<pk>\d+)$', DetailView.as_view(model=Vendeur,
						template_name='cyber/vendeur_detail.html'), name='vendeurDetail'),
	url(r'^vendeur/(?P<vendeur_id>\d+)/ventes/(page(?P<page>[0-9]+)/)?$', 'cyber.views.listVendeurVentes', name='listVendeurVentes'),
	url(r'^vendeur/(?P<vendeur_id>\d+)/ventesTkt/(page(?P<page>[0-9]+)/)?$', 'cyber.views.listVendeurVentesTkt', name='listVendeurVentesTkt'),
	url(r'^utilisateur/(?P<utilisateur_id>\d+)/connexions/(page(?P<page>[0-9]+)/)?$',
	'cyber.views.listUtilisateurConnexions', name='listUtilisateurConnexions'),
	url(r'^vendeur/(?P<pk>\d+)/modifier$', 'cyber.views.editVendeur', name='editVendeur'),
	url(r'^vendeur/creer$', 'cyber.views.newVendeur', name='newVendeur'),
	url(r'^vendre$', 'cyber.views.Vendre', name='Vendre'),
#    url(r'^vendeur/(?P<pk>\d+)/modifier/$', ''),
)
urlpatterns += staticfiles_urlpatterns()