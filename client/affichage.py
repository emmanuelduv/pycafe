# -*- coding: utf-8 -*-
from mytimer import MyTimer
import threading

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import urllib
import urllib2
import json
import gobject
import gtk
import time
import datetime
from decimal import *
from subprocess import Popen
import sys

#générique
import getpass

import os
import os.path
#Linux/Unix
import pwd

gobject.threads_init()

def responseToDialog(entry, dialog, response):
	dialog.response(response)
def focusLost(dialog, arg2):
	#print str(dialog)
	#print str(arg2)
	print 'focus perdu'
	dialog.hide()
	dialog.show()
	dialog.fullscreen()
	print 'reprise focus'
def getText(message_err):
	#base this on a message dialog
	dialog = gtk.MessageDialog(
		None,
		gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
		gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK, None)
	dialog.set_markup('Entrez votre <b>mot de passe</b>:')
	dialog.set_deletable(False)
	dialog.set_resizable(True)
#	dialog.resize(1000, 1000)
	dialog.fullscreen()
	#create the text input field
	entry = gtk.Entry()
	entry2 = gtk.Entry()
	#allow the user to press enter to do ok
	entry.connect("activate", responseToDialog, dialog, gtk.RESPONSE_OK)
	dialog.connect("focus-out-event", focusLost)
	#create a horizontal box to pack the entry and a label
	hbox = gtk.HBox()
	hbox.pack_start(gtk.Label("N° de ticket:"), False, 5, 5)
	hbox.pack_end(entry)
	#some secondary text
	text_2 = "Enregistrez le dans la configuration pour ne plus avoir à le rentrer"
	if 'message' in message_err:
		text_2 = '<b>'+message_err['message']+'</b> '+ text_2
	dialog.format_secondary_markup(text_2)
	#add it and show it
	dialog.vbox.pack_start(hbox, True, True, 0)

	hbox2 = gtk.HBox()
	hbox2.pack_start(gtk.Label("Mot de passe:"), False, 5, 5)
	hbox2.pack_end(entry2)
	dialog.vbox.pack_end(hbox2, True, True, 0)
	dialog.show_all()
	#go go go
	dialog.run()
	ticket_id = entry.get_text()
	ticket_identifiant = entry2.get_text()
	dialog.destroy()
	print 'ticket_id = ' + entry.get_text()
	print 'ticket_identifiant = '+ entry2.get_text()
	text = {'ticket_id': int(ticket_id), 'ticket_identifiant': ticket_identifiant}
	return text


class Affichage:
	def __init__(self):
		self.user_identifiant = ''
		self.user_id = -1
		self.user_mdp = ''
		self.user_login = ''
		self.ticket_id = ''
		self.ticket_identifiant = ''
		self.path_fichier_config = '~/.cafe/infoperso'
		self.path_fichier_config_tkt = '~/.cafe/infoticket'
		self.path_fichier_fenetre = 'fenetre2.glade'
		self.url = 'http://127.0.0.1:8088'
		self.session_close_cmd = '/usr/bin/gnome-session-quit --logout --force --no-prompt'
		if len(sys.argv) > 1:
			options = json.loads(sys.argv[1])
			if 'session_close_cmd' in options:
				self.session_close_cmd = options['session_close_cmd']

			if 'url_ctrl' in options:
				self.url = options['url_ctrl']

		self.b = gtk.Builder()
		self.b.add_from_file(self.path_fichier_fenetre)

		handlers = {"on_button1_clicked": self.oth_con,"on_button2_clicked": self.confirm_quit,"on_button3_clicked": self.configTkt	#config
		,"on_button_save_param_clicked": self.saveUserInfos, "on_button5_clicked": self.hideConfig
		, "on_checkbutton1_toggled": self.configPwd,"on_button4_clicked": self.hideOth_con#, "on_button6_clicked": self.hideOth_con
		, "on_button6_clicked": self.saveTicketInfos,"on_button6_clicked": self.hideConfigTkt, "window1_delete_event_cb": self.confirm_quit
		}
		self.b.connect_signals(handlers)
		self.w = self.b.get_object("window1")
#		self.w.__signals__ = {"delete-event", "override"}
#		self.w.connect("delete-event", self.confirm_quit)
		self.p = self.b.get_object("dialog1")
		self.c = self.b.get_object("messagedialog1")
		self.p_t = self.b.get_object("dialog2")	#Configuration du ticket

#		self.w.show_all()
#		self.readUserInfos()
		self.session_id = -1
		self.erreur = {}
		self.to_quit = 0
		while (self.session_id == -1):
			try:
				print 'readTicketInfos'
				self.readTicketInfos()
				self.w.set_title("Bienvenue "+self.user_login)
				print 'verifieInfos'
				ok = self.verifieInfos()
			except ValueError, e:
				self.erreur = {'message': 'Entrez un N° tde ticket et un mot de passe valide.'}
			except Exception, e:
				self.erreur = {'message': 'Erreur : '+str(e)}
				print e
		if ok == 0:
			self.w.show_all()
			#Configure GUI
			self.b.get_object("label_con_start").set_text(str(self.begin_time)[0:18])#connect time
#			self.w.__signals__ = {"delete-event", "override"}
#	                self.w.connect("delete-event", self.confirm_quit)
			if self.nb_con > 1:	#others connections button
				self.b.get_object("button1").set_label(str(self.nb_con)+' autres connexions')
			else:
				self.b.get_object("button1").hide()
			self.b.get_object("label_remain").set_text(' '+str(int(self.temps_total_restant))+':'+str(int((self.temps_total_restant-Decimal(int(self.temps_total_restant)))*60)))
			self.b.get_object("hbox3").hide()
			self.b.get_object("hbox4").hide()
			temps_restant = Decimal(self.infos['temps_restant'])
			temps = 1
			if temps_restant < self.temps_total_restant:
				temps = int(temps_restant*60)
			else:
				temps = int(self.temps_total_restant*60)
			print 'temps='+str(temps)
			self.t = MyTimer((temps/self.nb_con)-5, self.verifieInfos)
			self.t.start()
			self.t_decompte = threading.Thread(target=self.updateRemainingTime)
			self.t_decompte.start()
			p = Popen('python helper.py', shell=True)
		else:
			print 'error, disconection'
			self.quit()
		gtk.main()

	def updateRemainingLabel(self, text):
		l_r = self.b.get_object("label_remain")
		l_r.set_text(text)
		if text.startswith(' 0:'):#remaining time in red if < 1 minute
			try:
				s = l_r.get_style().copy()
				s.fg[gtk.STATE_NORMAL] = l_r.get_colormap().alloc(65535, 0, 0)
				l_r.set_style(s)
				self.w.set_opacity(1)
			except Exception, e:
				print e

	def updateRemainingTime(self):
		delta = Decimal('0.016265')#One second in minute
		delta_9 = Decimal('0.150')
		delta_8 = Decimal('0.133')
		visible = False
		while self.temps_total_restant_affiche >= delta and self.to_quit == 0:
			minutes = str(int(self.temps_total_restant_affiche))
			secondes = str(int((self.temps_total_restant_affiche-Decimal(int(self.temps_total_restant_affiche)))*60))
			if len(secondes) < 2:
				secondes = '0'+secondes
			gobject.idle_add(self.updateRemainingLabel, ' '+minutes+':'+secondes)
			self.temps_total_restant_affiche -= delta
			print 'updateRemainingTime...'
			#if (self.temps_total_restant_affiche >= delta_8 and self.temps_total_restant_affiche <= delta_9):	#Confirm remaining time
			if (self.temps_total_restant_affiche <= delta):
				print 'Check real remaining time : '
				self.verifieInfos()
				print str(self.temps_total_restant_affiche)
			threading.Event().wait(1)
			#p = subprocess.Popen(['/usr/bin/sleep', '1'], stdout=subprocess.PIPE)
			#p.stdout.read()
			print str(self.temps_total_restant_affiche) + ' remaining'
			visible = False
			try:
				visible = self.w.get_visible()
			except Exception, e:
				print e
			if (visible == False):
				self.to_quit = 1
		print 'updateRemainingTime : ended'
		print 'exiting session'
		self.quit(None)

	def userName(self):
		return pwd.getpwuid(os.getuid()).pw_name
	#Générique
	#	return getpass.getuser()

	def demandeMDP(self):
		mdp = getText(self.erreur)
		return mdp

	def retourServeur(self, donnees, url):
		print 'envoi des données : ' + str(json.dumps(donnees))
		req = urllib2.Request(url, urllib.urlencode({'infos':json.dumps(donnees)}))
		try:
			h = urllib2.urlopen(req)
		except urllib2.URLError, e:
			print 'Échec de la liaison avec le serveur %s(%s)' % (url, e.reason)
			self.code_erreur = -1
			self.erreur = {'message' : 'Échec de la liaison avec le serveur '+str(url)+'('+str(e.reason)+')'}
			return -1
		except urllib2.HTTPError, e:
			print 'Problème : erreur %s' % (str(e.code))
			self.erreur = json.loads(e.read())
			self.code_erreur = e.code
		except Exception, e:
			print str(e)
			return -1
		d = h.read()
		print 'reçu : '+d
		self.infos = json.loads(d)
		if 'message' in self.infos:
			self.message = self.infos['message']
		if 'code' in self.infos:
			self.code_erreur = self.infos['code']
		else:
			print "Pas de code, message d'erreur?"
			if 'message' in self.infos:
				print 'oui : ' + self.infos['message']
				self.erreur = self.infos
			return 1
		return 0

	def readTicketInfos(self):
		config = None# l = p.stdout.read
		fichier = os.path.expanduser(self.path_fichier_config_tkt)
		self.user_login = self.userName()
		try:
			if not os.path.exists(fichier):
				self.configTkt(None)
			taille = os.path.getsize(fichier)
			if taille < 10 or taille > 10000:
				raise Exception('Vérifier le fichier.')
			f = open(fichier, 'r')
			config = json.loads(f.read())
		except:
			print 'pas de N° ticket ni mot de passe'
			self.hideConfigTkt(None)
			config = self.demandeMDP()
		self.ticket_id = config['ticket_id']
		self.b.get_object("entry_id_ticket").set_value(self.ticket_id)
		self.ticket_identifiant = config['ticket_identifiant']
		self.b.get_object("entry_identifiant_ticket").set_text(self.ticket_identifiant)
		
		self.config_help = 0	#1 = hidden!
		if 'config_help' in config:
			self.config_help = config['config_help']
			if self.config_help == 1:
				self.b.get_object("check_help").set_active()

	def saveTicketInfos(self, bouton):
		_ticket_id = self.b.get_object("entry_id_ticket").get_value_as_text()
		_ticket_identifiant = self.b.get_object("entry_identifiant_ticket").get_text()
		_config_help = 0	#not hidden
		if self.b.get_object("check_help").get_active():
			_config_help = 1
		self.ticket_id = _ticket_id
		self.ticket_identifiant = _ticket_identifiant
		self.config_help = _config_help
		if self.b.get_object("check_identifiant_ticket").get_active():
			config = {'ticket_id':self.ticket_id, 'config_help': self.config_help, 'ticket_identifiant':self.ticket_identifiant}
		else:
			config = {'ticket_id':self.ticket_id, 'config_help': self.config_help}
		fichier = os.path.expanduser(self.path_fichier_config_tkt)
		if not os.path.exists(os.path.dirname(fichier)):
			os.makedirs(os.path.dirname(fichier))
		f = open(fichier, 'w')
		f.write(json.dumps(config))
		self.hideConfigTkt(bouton)

	def readUserInfos(self):
		fichier = os.path.expanduser(self.path_fichier_config)
		if not os.path.exists(os.path.dirname(fichier)):
			self.config(None)
		taille = os.path.getsize(fichier)
		if taille < 10 or taille > 10000:
			raise Exception('Vérifier le fichier.')
		f = open(fichier, 'r')
		config = json.loads(f.read())
		self.user_identifiant = config['user_identifiant']
		self.b.get_object("entry_identifiant").set_text(self.user_identifiant)
		self.user_id = config['user_id']
		self.b.get_object("entry_id").set_text(self.user_id)
		self.user_login = self.userName()
		self.b.get_object("entry_login").set_text(self.user_login)
		if 'user_mdp' in config:
			self.user_mdp = config['user_mdp']
		else:
			self.user_mdp = self.demandeMDP()
		self.b.get_object("entry_pwd").set_text(self.user_mdp)

	def saveUserInfos(self, bouton):
		_user_id = self.b.get_object("entry_id").get_text()
		_user_identifiant = self.b.get_object("entry_identifiant").get_text()
		_user_pwd = self.b.get_object("entry_pwd").get_text()
		if len(_user_id) < 1 and len(_user_identifiant) < 1:
			self.b.get_object("label_pb_config").set_text("Merci de remplir tout (login non modifiable)")
			return -1
		else:
			self.b.get_object("label_pb_config").set_text("")
		self.user_id =  _user_id
		self.user_identifiant = _user_identifiant
		self.user_mdp = _user_pwd
		fichier = os.path.expanduser(self.path_fichier_config)
		if not os.path.exists(os.path.dirname(fichier)):
			os.makedirs(os.path.dirname(fichier))
		f = open(fichier, 'w')
		if self.b.get_object("checkbutton1").get_active():
			config = {'user_identifiant':self.user_identifiant, 'user_id':self.user_id,'user_mdp':self.user_mdp}
		else:
			config = {'user_identifiant':self.user_identifiant, 'user_id':self.user_id}

		f.write(json.dumps(config))
		self.hideConfig(bouton)

	def verifieInfos(self):
#		if self.session_id == -1:
#			config = {'action':'start', 'user_login':self.user_login, 'user_identifiant':self.user_identifiant, 'user_id':self.user_id,'user_mdp':self.user_mdp}
#		else:
#			config = {'action':'cont' , 'user_login':self.user_login, 'user_identifiant':self.user_identifiant, 'user_id':self.user_id,'user_mdp':self.user_mdp, 'session_id':self.session_id, 'session_identifiant':self.session_identifiant}

		if self.session_id == -1:
			config = {'action':'tkt_start', 'user_login':self.user_login, 'ticket_id':self.ticket_id, 'ticket_identifiant':self.ticket_identifiant}
		else:
			config = {'action':'tkt_cont' , 'user_login':self.user_login, 'ticket_id':self.ticket_id, 'ticket_identifiant':self.ticket_identifiant, 'session_id':self.session_id}
		print 'verifieInfos'
		r = self.retourServeur(config, self.url)
		if r != 0:
			if self.session_id != -1:
				return self.quit(None)
			return 1
		else:
			if 'temps_restant' in self.infos:
				self.temps_restant = self.infos['temps_restant']
			else:
				self.temps_restant = 0
				if self.session_id == -1:
					raise Exception('Impossible de continuer la session.')
				else:
					self.quit(None)
			self.session_id = -1
			if 'connexions' in self.infos:
				connexions = self.infos['connexions']
				self.nb_con = 0
				for c in connexions:
					self.nb_con += 1
					if c['courante'] == 1:
						if self.session_id != -1 and (self.session_id != c['id'] or self.session_identifiant != c['identifiant']):	#Si on reçoit une autre session : problème!
							self.quit(None)
							return -1
						if self.session_id == -1:	#On enregistre l'heure de début
							self.begin_time = datetime.datetime.now()
						self.session_id = c['id']
#						self.session_identifiant = c['identifiant']
						self.date_fin = datetime.datetime.strptime(c['date_fin'][0:18], "%Y-%m-%d %H:%M:%S")#attention format date
						pc = c['pc']
						pc_temps_mini = Decimal(pc['temps_mini_facture'])
						#self.temps_total_restant = Decimal(self.infos['minutes_total_restantes'])
						self.temps_total_restant = Decimal(self.infos['minutes_total_restantes'])
						self.temps_total_restant_affiche = self.temps_total_restant	#Decimal(self.infos['minutes_total_restantes'])
						if self.temps_total_restant < pc_temps_mini:
							print "Reste : "+str(self.temps_total_restant) + '(pc_temps_mini='+str(pc_temps_mini)+')'
#							self.t.stop()
#							self.t_fin = threading.Timer(int(self.temps_total_restant*Decimal(60)), self.quit)
#							self.t_fin.start()
			if self.session_id == -1:
				return -1
			self.dernier_pointage = datetime.datetime.now()
			return 0

	def oth_con(self, bouton):
		l = ""
		try:
			for s in self.infos.sessions:
				if s.courante == 0:
					c = s.date_debut+", "+s.pc.identifiant
					l = l+c+"\n"
		except:
			print 'Problème!'
		if len(l) < 1:
			l = '--Aucune autre connexion--'
		self.b.get_object("label_list_con").set_text(l)
		self.c.show_all()

	def config(self, bouton):
		self.p.show_all()

	def configTkt(self, bouton):
		self.p_t.show_all()

	def hideConfigTkt(self, bouton):
		self.p_t.hide()

	def hideConfig(self, bouton):
		self.p.hide()
		self.b.get_object("label_pb_config").set_text("")

	def hideOth_con(self, bouton):
		self.c.hide()

	def configPwd(self, bouton):
		if self.b.get_object("checkbutton1").get_active():
			self.b.get_object("entry_pwd").set_text("")
			self.b.get_object("entry_pwd").set_editable(False)
		else:
			self.b.get_object("entry_pwd").set_editable(True)
		print "configPwd"
	def confirm_quit(self, bouton):
		d=gtk.MessageDialog(buttons=gtk.BUTTONS_OK_CANCEL, message_format="Quitter (ferme la session)?")
		r=d.run()
		if r == gtk.RESPONSE_OK:
			self.quit(None)
		else:
			return True

	def quit(self, bouton):
		self.to_quit = 1
		#config = {'action':'quit' , 'user_login':self.user_login, 'user_identifiant':self.user_identifiant, 'user_id':self.user_id,'user_mdp':self.user_mdp, 'session_id':self.session_id, 'session_identifiant':self.session_identifiant}
		config = {'action':'tkt_quit', 'user_login':self.user_login, 'ticket_id':self.ticket_id, 'ticket_identifiant':self.ticket_identifiant, 'session_id':self.session_id}
		self.retourServeur(config, self.url)
		print "fini!"
		try:	#if called from the t thread (in verifieInfos in certain conditions) will fail
			self.t.stop()
			print 'check timer ended'
		except Exception, e:
			print str(e)
			print 'ending check timer failed, continuing disconnecting process'

		try:	#if called from the t_decompte thread (in updateRemainingTime) will fail
			self.t_decompte.join(1.5)
			print 'clock thread ended'
		except Exception, e:
			print str(e)
			print 'ending clock thread failed, continuing disconnection process'
		#self.t_decompte.stop()
		#fermer la session
		try:
			p = Popen(self.session_close_cmd, shell=True)
			print 'logout command launched'
		except Exception, e:
			print str(e)
			print 'failed to run logout command, exiting anyway. Workaround : add a logout command after running this program'
		try:
			quit(bouton)
		except Exception, e:
			print str(e)
			print 'quit(bouton) failed'
			quit()

if __name__ == '__main__':
	a = Affichage()
#p.show_all()
#c.show_all()
