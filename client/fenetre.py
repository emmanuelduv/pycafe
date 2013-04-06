import gtk
b = gtk.Builder()
b.add_from_file("/home/emmanuel/progs/fenetre2.glade")

def oth_con(bouton):
  print "A faire"

def config(bouton):
  print "config A faire"

handlers = {"on_button1_clicked": oth_con,"on_button2_clicked": quit,"on_button3_clicked": config}
b.connect_signals(handlers)
w = b.get_object("window1")

w.show_all()
gtk.main()
