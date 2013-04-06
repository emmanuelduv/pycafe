# -*- coding: utf-8 -*-
import json
import gtk
import subprocess
class PyCafeHelper:
	def button_clicked(self, widget, data=None):
		print data
		if 'cmd' in self.config['bts'][data]:
			print self.config['bts'][data]['cmd']
			p = subprocess.Popen(self.config['bts'][data]['cmd'], shell=True)

	def __init__(self, config_file="config.json"):
		f = open(config_file, 'r')
		self.config = json.loads(f.read())
		self.win = gtk.Window()
		self.win.connect("destroy", gtk.main_quit)
		self.win.set_title("Choisissez quoi lancer. Vous pouvez réduire ou fermer cette fenêtre et accéder à une session normale")
		self.table = gtk.Table(self.config['lig'], self.config['col'])
		self.win.add(self.table)
		bts = self.config['bts']
		for lig in range(self.config['lig']):
			for col in range(self.config['col']):
				if 'bt_'+str(lig)+str(col) in bts:
					bt = bts['bt_'+str(lig)+str(col)]
					btn=None
					if 'image' in bt:	#http://www.pygtk.org/pygtk2tutorial/ch-ButtonWidget.html
						image = gtk.Image()
						image.set_from_file(bt['image'])
						label = gtk.Label(bt['label'])
						box1 = gtk.VBox(False, 0)
						box1.pack_start(image, False, False, 3)
						box1.pack_start(label, False, False, 3)
						image.show()
						label.show()
						btn = gtk.Button()
						btn.add(box1)
						box1.show()
					else:
						btn = gtk.Button(bt['label'])
					#make a gdk.color for red
					if 'color' in bt:	#http://stackoverflow.com/questions/1241020/gtk-create-a-colored-regular-button
						map = btn.get_colormap()
						color = map.alloc_color(bt['color'])
						#copy the current style and replace the background
						style = btn.get_style().copy()
						style.bg[gtk.STATE_NORMAL] = color
						#set the button's style to the one you created
						btn.set_style(style)
					btn.set_name('bt_'+str(lig)+str(col))
					btn.connect("clicked", self.button_clicked, 'bt_'+str(lig)+str(col))
					self.table.attach(btn, col, col+1, lig, lig+1)
					btn.show()
				else:
					print 'bt_'+str(lig)+str(col) + ' not found!'
		self.table.show()
		self.win.show()
		self.win.resize(1024, 768)
		gtk.main()

if __name__ == '__main__':
	a = PyCafeHelper()
