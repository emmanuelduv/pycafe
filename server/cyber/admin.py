from cyber.models import Cyber, PC, Utilisateur
#from cyber.models import PC
from django.contrib import admin

class PCInLine(admin.TabularInline):
	model = PC
	extra = 2

class CyberAdmin(admin.ModelAdmin):
	inlines = [PCInLine]

admin.site.register(Cyber, CyberAdmin)
admin.site.register(Utilisateur)