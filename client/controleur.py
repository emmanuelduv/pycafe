# -*- coding: utf-8 -*-
import sys
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
from urlparse import parse_qs
from cgi import parse_header,parse_multipart
import subprocess
import psutil

import threading
import urllib
import urllib2
import json
import sys
from decimal import *
import datetime
from datetime import timedelta

from mytimer import MyTimer
#controleur.py {"PC_id": 1, "PC_identifiant": "11", "server_url_start": "http://192.168.1.2/start", "server_url_cont": "http://192.168.1.2/cont", "server_url_clo": "http://192.168.1.2/cont", "port": 8080, "session_close_cmd": "/sbin/reboot"}
#{"PC_id": 12, "PC_identifiant": "3215674897", "server_url_start": "http://localhost:8000/session_start", "server_url_cont": "http://localhost:8000/session_continue", "server_url_clo": "http://localhost:8000/session_continue", "port": 8080, "session_close_cmd": "/sbin/reboot"}


class Connexion:
	local_connexions = {}
	options = json.loads(sys.argv[1])
#{"PC_id": 12, "PC_identifiant": "3215674897", "server_url_start": "http://192.168.1.2/start"
#, "server_url_cont": "http://192.168.1.2/cont", "server_url_clo": "http://192.168.1.2/cont", "port": 8080
#, "session_close_cmd": "/sbin/reboot"}
	if 'server_url_start' in options:
		server_url_start = options['server_url_start']
	else:
		server_url_start = 'http://192.168.1.2/start'

	if 'server_url_cont' in options:
		server_url_cont = options['server_url_cont']
	else:
		server_url_cont = 'http://192.168.1.2/cont'

	if 'server_url_clo' in options:
		server_url_clo = options['server_url_clo']
	else:
		server_url_clo = 'http://192.168.1.2/cont'

	if 'port' in options:
		port = options['port']
	else:
		port = 8080

	if 'session_close_cmd' in options:
		session_close_cmd = options['session_close_cmd']
	else:
		session_close_cmd = '/sbin/reboot'

	if 'PC_id' in options:
		PC_id = int(options['PC_id'])
	else:
		print'Pas de PC_id dans les paramètres, il est obligatoire ("PC_id": <int>)'
		quit()

	if 'PC_identifiant' in options:
		PC_identifiant = options['PC_identifiant']
	else:
		print'Pas de PC_identifiant dans les paramètres, il est obligatoire ("PC_identifiant": <int>)'
		quit()
	if 'allowed_users' in options:
		allowed_users = options['allowed_users']
	else:
		allowed_users = {}
	kill_process_next_check = 0	#Kill processes next check
	connected_users = {}	#connected users

	def __init__(self, login, mdp, identifiant, user_id):
		self.login = login
		self.user_id = user_id
		self.identifiant_user = identifiant
		self.mdp = mdp
		self.code_erreur = 0
		self.message = 'OK'
		self.type_session = 'user'
		self.erreur = {}
		self.t_fin = None
		if self.start() != -1:
			Connexion.local_connexions[self.type_session+str(self.id)] = self
			Connexion.connected_users[self.login] = self.type_session+str(self.id)
			return
		else:
			raise Exception('Connexion impossible')

	def __init__(self, login, ticket_identifiant, ticket_id):#r['user_login'], r['ticket_identifiant'], r['ticket_id']
		self.login = login
		self.ticket_identifiant = ticket_identifiant
		self.ticket_id = ticket_id
		self.code_erreur = 0
		self.message = 'OK'
		self.type_session = 'tkt'
		self.t_fin = None
		if self.start() != -1:
			Connexion.local_connexions[self.type_session+str(self.id)] = self
			Connexion.connected_users[self.login] = self.type_session+str(self.id)
			return
		else:
			raise Exception('Connexion impossible : ('+self.erreur['message']+')')

#	@staticmethod
	def poursuit_tkt(login, ticket_identifiant, ticket_id, session_id, tkt):
		c = Connexion.find(session_id, tkt)
		if c is not None:
			if c.login != login or c.ticket_identifiant != ticket_identifiant or c.ticket_id != ticket_id or c.id != session_id:
				return c.close()
			else:
				c.poursuit()
				return c
	poursuit_tkt = staticmethod(poursuit_tkt)

	def check_conn_users():
		nb_p_to_kill = 0
		p=subprocess.Popen(['/bin/ps', '-e', '-o', 'user,uid,pid,command'], stdout=subprocess.PIPE)	#wmctrl -lp pour lister les fenêtres...
		l = p.stdout.readline()	#header line
		l = ' '.join((p.stdout.readline()).split())
		while len(l) > 1:
			l_d = l.split(' ', 4)
			process = psutil.Process(int(l_d[2]))
			uid = int(l_d[1])
			if process.username in Connexion.allowed_users or len(Connexion.allowed_users) == 0 or process.username in Connexion.connected_users or uid < 1000:
				print 'Autorisé ou connecté ou tout le monde autorisé ou < 1000 : '+l
			else:
				print 'Non autorisé ni connecté: '+l
				if Connexion.kill_process_next_check == 1:
					process.kill()	#Last check found one unallowed process : this time kill it
				else:
					nb_p_to_kill += 1	#At least one process to kill at next check
			l = ' '.join((p.stdout.readline()).split())
		if nb_p_to_kill > 0:
			Connexion.kill_process_next_check = 1
		else:
			Connexion.kill_process_next_check = 0
	check_conn_users = staticmethod(check_conn_users)

#	@staticmethod
	def close_tkt(login, ticket_identifiant, ticket_id, session_id, tkt):
		c = Connexion.find(session_id, tkt)
		if c is not None:
			if c.login != login or c.ticket_identifiant != ticket_identifiant or c.ticket_id != ticket_id or c.id != session_id:
				return -1
			else:
				c.close()
				return c
	close_tkt = staticmethod(close_tkt)

#	@staticmethod
	#def poursuit(login, identifiant, connexion_id, connexion_identifiant):
		#c = Connexion.find(connexion_id)
		#if c is not None:
			#if c.login != login or c.identifiant_user != identifiant or c.identifiant != connexion_identifiant or c.id != connexion_id:
				#c.close()
				#return c
			#else:
				#c.poursuit()
				#return c
	#poursuit = staticmethod(poursuit)

#	@staticmethod
	#def close(login, identifiant, connexion_id, connexion_identifiant):
		#c = Connexion.find(connexion_id)
		#if c is not None:
			#if c.login != login or c.identifiant_user != identifiant or c.identifiant != connexion_identifiant or c.id != connexion_id:
				#return -1
			#else:
				#c.close()
				#return c
	#close = staticmethod(close)

#	@staticmethod
	def find(connexion_id, tkt):
		if tkt+str(connexion_id) in Connexion.local_connexions:
			return Connexion.local_connexions[tkt+str(connexion_id)]
		else:
			return None
	find = staticmethod(find)

	def start(self):
		donnees = None
		if self.type_session == 'tkt':
			donnees = {'PC_id':Connexion.PC_id, 'login': self.login
			, 'ticket_id': self.ticket_id, 'ticket_identifiant': self.ticket_identifiant
			, 'PC_identifiant': Connexion.PC_identifiant}
		else:
			donnees = {'PC_id':Connexion.PC_id, 'user_id': self.user_id
			, 'mdp': self.mdp, 'login': self.login, 'user_identifiant': self.identifiant_user
			, 'PC_identifiant': Connexion.PC_identifiant}
		retour = self.retourServeur(donnees, Connexion.server_url_start)
		self.id = -1
		if 'message' in self.erreur:
			return -1
		if 'connexions' in self.infos:
			connexions = self.infos['connexions']
			for c in connexions:
				if c['courante'] == 1:
					self.id = c['id']
					self.date_fin = datetime.datetime.strptime(c['date_fin'][0:18], "%Y-%m-%d %H:%M:%S")#attention format date
		else:
			if retour <> 0:
				return -1
		if retour <> 0:
			return self.close()
		if 'temps_restant' in self.infos:
			self.temps_restant = Decimal(self.infos['temps_restant'])
		else:
			return self.close()

		if self.id == -1:
			return -1
		if self.temps_restant == 0:
			return self.close()
		self.t = MyTimer(int(self.temps_restant)*60/len(self.infos['connexions'])-5, self.testerValidite)
		self.t.start()
		self.dernier_pointage = datetime.datetime.now()
		return 0

	def poursuit(self):
		donnees = None
		if self.type_session == 'tkt':
			donnees = {'PC_id':Connexion.PC_id, 'login': self.login
			, 'ticket_id': self.ticket_id, 'ticket_identifiant': self.ticket_identifiant
			, 'PC_identifiant': Connexion.PC_identifiant, 'session_id': self.id}
		else:
			donnees = {'PC_id':Connexion.PC_id, 'user_id': self.user_id
			, 'mdp': self.mdp, 'login': self.login, 'user_identifiant': self.identifiant_user
			, 'PC_identifiant': Connexion.PC_identifiant, 'session_id': self.id}
		retour = self.retourServeur(donnees, Connexion.server_url_cont)
		if retour <> 0:
			return -1
		if 'temps_restant' in self.infos:
			self.temps_restant = Decimal(self.infos['temps_restant'])
		else:
			return self.close()
		id = -1
		if 'connexions' in self.infos:
			connexions = self.infos['connexions']
			for c in connexions:
				if c['courante'] == 1:
					id = c['id']
					if id == self.id:
						self.date_fin = datetime.datetime.strptime(c['date_fin'][0:18], "%Y-%m-%d %H:%M:%S")#attention format date
					else:
						return self.close()
					pc = c['pc']
					pc_temps_mini = Decimal(pc['temps_mini_facture'])
					temps_total_restant = Decimal(self.infos['minutes_total_restantes'])
#					if temps_total_restant < pc_temps_mini:
					print "Reste : "+str(temps_total_restant) + '(pc_temps_mini='+str(pc_temps_mini)+')'
					self.t.stop()
					if self.t_fin != None:
						self.t_fin.cancel()
						self.t_fin = None
					self.t_fin = threading.Timer(int(temps_total_restant*Decimal(60))+44, self.testerValidite)
					self.t_fin.start()

		if id == -1 or id != self.id:
			return -1
		self.t._tempo = int(self.temps_restant)*60/len(self.infos['connexions'])-5
		self.dernier_pointage = datetime.datetime.now()
		return 0

	def close(self):
		donnees = None
		if self.type_session == 'tkt':
			donnees = {'PC_id':Connexion.PC_id, 'login': self.login
			, 'ticket_id': self.ticket_id, 'ticket_identifiant': self.ticket_identifiant
			, 'PC_identifiant': Connexion.PC_identifiant, 'session_id': self.id}
		else:
			donnees = {'PC_id':Connexion.PC_id, 'user_id': self.user_id
			, 'mdp': self.mdp, 'login': self.login, 'user_identifiant': self.identifiant_user
			, 'PC_identifiant': Connexion.PC_identifiant, 'session_id': self.id}
		retour = self.retourServeur(donnees, Connexion.server_url_clo)
		self.t.stop()
		if self.t_fin != None:
			self.t_fin.cancel()
			self.t_fin = None

		del Connexion.local_connexions[self.type_session+str(self.id)]
		del Connexion.connected_users[self.login]
		if retour <> 0:
			return -1
		else:
			return 0
		return -1
	def retourServeur(self, donnees, url):
		req = urllib2.Request(url, urllib.urlencode({'donnees':json.dumps(donnees)}))
		print 'envoi de ' + str(json.dumps(donnees))+ ' vers ' +str(url)
		h=None
		content = None
		self.erreur = {}
		try:
			h = urllib2.urlopen(req)
		except urllib2.HTTPError, e:
			print 'Problème : erreur %s' % (str(e.code))
			content = json.loads(e.read())
			print content
			self.code_erreur = e.code
		except urllib2.URLError, e:
			print 'Echec de la liaison avec le serveur %s(%s)' % (url, e.reason)
#			self.erreur = json.loads(e.read())
			self.erreur = 'Echec de la liaison avec le serveur '+str(url)+'('+str(e.reason)+')'
			self.code_erreur = -1
			return -1
		if content != None:
			self.erreur = content
		else:
			self.infos = json.loads(h.read())
		print self.infos
		if 'code' in self.infos:
			self.code_erreur = self.infos['code']
		else:
			return 1
		if 'message' in self.infos:
			self.message = self.infos['message']
		if 'connexions' in self.infos:
			for c in self.infos['connexions']:
				if 'pc' in c:
					pc = c['pc']
					if 'id' in pc:
						del pc['id']
		return 0

	def testerValidite(self):
		if(datetime.datetime.now() >= self.dernier_pointage + timedelta(seconds=1+int(self.temps_restant*60))):
			print 'Session expirée'
			self.close()
		print 'testerValidite : Ok'


	def deconnecter(self):
		print 'deconnecter : À faire'

class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.end_headers()
		message = "<html><head><title>Bienvenue</title></head>"
		message += "<body><p>Programme de contrôle en cours d'exécution. Cette page ne fait rien, il faut POSTer les donnés</p>"
		message += "<form method=\"post\"><textarea name=\"infos\">{\"action\": \"start\", \"user_identifiant\": 123456789, \"user_id\": 1, \"user_mdp\": \"toto\"}</textarea>"
		message += "<input type=\"submit\"></form></body></html>"
		self.wfile.write(message)
		self.wfile.write('\n')
		return
	
	def do_POST(self):
		length=0
		ctype, pdict = parse_header(self.headers.getheader('content-type'))
		if ctype == 'multipart/form-data':
			postvars = parse_multipart(self.rfile, pdict)
			print 'multipart/form-data, reçu:'
			print postvars
		elif ctype == 'application/x-www-form-urlencoded':
			length = int(self.headers.getheader('content-length'))
			postvars = parse_qs(self.rfile.read(length), keep_blank_values=1)
			print 'application/x-www-form-urlencoded, reçu:'
			print postvars
		else:
			postvars = {}
		r = json.loads(postvars['infos'][0])

		c = None
		if 'action' in r:
			a = r['action']
			print a
			if a == 'start':
				print 'Démarrage de la session...'
				try:
					c = Connexion(r['user_login'], r['user_mdp'], r['user_identifiant'], r['user_id'])
				except Exception, e:
					erreur = {'message': str(e)}
					print 'Ko'
				print 'Ok'
			#elif a == 'cont':
				#c = Connexion.find(r['session_id'], 'user')
				#if c is None:
					#self.send_response(400)
					#self.end_headers()
					#return
				#retour = c.poursuit(r['user_login'], r['user_identifiant'], r['session_id'], r['session_identifiant'])#login, identifiant, connexion_id, connexion_identifiant
			elif a == 'tkt_start':
				print 'Démarrage de la session avec le ticket...'
				try:
					c = Connexion(r['user_login'], r['ticket_identifiant'], r['ticket_id'])
					erreur = c.erreur
					print 'Ok'
				except Exception, e:
					erreur = {'message': str(e)}
					print 'Ko'
			elif a == 'tkt_cont':
				c = Connexion.poursuit_tkt(r['user_login'], r['ticket_identifiant'], r['ticket_id'], r['session_id'], 'tkt')#login, ticket_identifiant, ticket_id, session_id, tkt
				if c is None:
					erreur = {"message": "Problem : impossible to continue!"}
				else:
					erreur = c.erreur
			elif a == 'tkt_quit':
				c = Connexion.close_tkt(r['user_login'], r['ticket_identifiant'], r['ticket_id'], r['session_id'], 'tkt')
				if c is None:
					erreur = {"message": "Problem : impossible to quit!"}
				else:
					erreur = c.erreur
			else:
				self.send_response(400)
				self.end_headers()
				return
		else:
			self.send_response(400)

		self.send_response(200)
		self.end_headers()
		if 'message' in erreur:
			print str(erreur)
			message = json.dumps( erreur)
		else:
			message = json.dumps( c.infos)
		self.wfile.write(message)
		self.wfile.write('\n')
		if a == 'tkt_quit':
			c = None
		return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""

if __name__ == '__main__':
	server = ThreadedHTTPServer(('localhost', 8088), Handler)
	Connexion.t = MyTimer(600, Connexion.check_conn_users)
	Connexion.t.start()
	print 'Starting server, use <Ctrl-C> to stop'
	server.serve_forever()
