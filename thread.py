from time import sleep
import types
from PyQt5.QtCore import pyqtSignal, QThread, QMutex

#打印读取线程
import debugpy
class PrintThread(QThread):
	printSig = pyqtSignal(list)

	def __init__(self, name):
		super().__init__()
		self.name = name
		self.state = 0
		self.mutex = QMutex()

	def run(self):
		from manager import manager
		debugpy.debug_this_thread()
		while True:
			self.mutex.lock()
			#检测项目是否存在
			if self.name not in manager.projs.keys():
				self.state = 0
				self.mutex.unlock()
				print('打印线程：项目不存在', self.name)
				break
			#检测线程任务状态
			if self.state == 0:
				self.mutex.unlock()
				sleep(1)
				continue
			#检测进程是否存在
			proj = manager.projs[self.name]
			if proj.process == None:
				self.mutex.unlock()
				sleep(0.5)
				continue
			self.mutex.unlock()
			output = proj.process.stdout.readline() #阻塞
			if output:
				sleep(0.05)
				#print('打印', self.name, len(output), output)
				self.printSig.emit([self.name, output])
			else:
				self.mutex.lock()
				if proj.process.poll() is not None:
					self.state = 0
					print('进程终止，暂停打印线程', self.name, output)
					self.mutex.unlock()
					self.printSig.emit([self.name, None])
					continue
				self.mutex.unlock()

#---------------------------------------------------------------
class WorkThread(QThread):
	executor = None
	func = None
	callback = None
	doneSig = pyqtSignal(types.FunctionType)

	def __init__(self):
		super().__init__()

	def set(self, func, callback):
		self.func = func
		self.callback = callback
		self.start()
	
	def run(self):
		if self.func:
			self.func(self.executor)
			if self.callback:
				self.doneSig.emit(self.callback)
			self.func = None