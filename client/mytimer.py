import threading
class MyTimer:
	def __init__(self, tempo, target, args= [], kwargs={}):
		self._target = target
		self._args = args
		self._kwargs = kwargs
		self._tempo = tempo
		print self._tempo
		print self._target

	def _run(self):
		self._timer = threading.Timer(self._tempo, self._run)
		self._timer.start()
		print self._tempo
		print self._target
		self._target(*self._args, **self._kwargs)
		
	def start(self):
		self._timer = threading.Timer(self._tempo, self._run)
		self._timer.start()
		print 'demarrage Timer'

	def stop(self):
		self._timer.cancel()
