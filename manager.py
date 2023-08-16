import shutil
import subprocess
from PyQt5.QtWidgets import QMdiSubWindow
from PyQt5.QtGui import QColor
from common import *
from project import ProjData, ProjAny
from projGalTransl import ProjGalTransl

ProjTypeList = [
	ProjGalTransl,
	ProjAny
]

#---------------------------------------------------------------
class TransManager:
	#mainConfig:QSettings = None
	workpath = ''
	origpath = ''
	transpath = ''
	preCmd = ''
	projs = {}
	waitList = [] #管理器wait列表
	projsWaitList = set() #所有项目wait的集合
	mainWindow = None

	printEncode = 'GBK'
	tooltype = 0
	#mutex = None

	#初始化
	def init(self):
		self.projs.clear()
		if self.workpath == '':
			print('\033[33m没有选择工作目录\033[0m')
			return
		createFolder(self.workpath, ['projs', 'orig', 'trans', 'sampleProj'])
		self.origpath = os.path.join(self.workpath, 'orig')
		self.transpath = os.path.join(self.workpath, 'trans')

	#刷新所有项目
	def refreshProjs(self):
		#self.projs.clear()
		#检查projs
		existList = []
		projsPath = os.path.join(self.workpath, 'projs')
		for name in os.listdir(projsPath):
			path = os.path.join(projsPath, name) 
			if os.path.isfile(path): continue
			existList.append(name)
			if name not in self.projs.keys():
				#新建ProjData
				proj = ProjData(name, path)
				self.projs[name] = proj
				#self.projs[name].startThread(self.printCallback)
				#创建控制
				cls = manager.getCtrlClass()
				proj.ctrl = cls(proj)
			self.projs[name].ctrl.preCmd = self.preCmd
		#删除不存在的项目
		for name in list(self.projs.keys()):
			if name not in existList:
				del self.projs[name]

	def getCtrlClass(self):
		return ProjTypeList[self.tooltype]
	
	#新加项目
	def createProj(self, name):
		src = os.path.join(self.workpath, 'sampleProj')
		dst = os.path.join(self.workpath, 'projs', name)
		shutil.copytree(src, dst)
	
	#设置命令行
	def setPreCmd(self, toolpath):
		self.preCmd = self.getCtrlClass().getPreCmd(toolpath)
		return self.preCmd

	#---------------------------------------------------------------
	#启动进程
	def start(self, proj:ProjData):
		if proj.process == None:
			#打印线程
			proj.startThread(self.printCallback)
			#处理进程
			command = proj.ctrl.getCmd()
			print('启动进程', command)
			proj.process = subprocess.Popen(command, \
					stdout=subprocess.PIPE, stderr=subprocess.STDOUT, \
					text=True, shell=True, encoding=self.printEncode, bufsize=1)
		proj.ctrl.showColor(QColor(84, 179, 69))
	
	#结束进程
	def stop(self, proj:ProjData):
		proj.printThread.mutex.lock()
		if proj.process:
			print('结束进程', proj.name)
			proj.process.terminate()
			proj.process = None
			#proj.ctrl.window = None
		proj.printThread.state = 0 #设置打印线程状态
		proj.printThread.mutex.unlock()
		proj.ctrl.showColor(QColor(255, 255, 255))
		if proj.autoStart:
			if self.mainWindow:
				self.mainWindow.startProj(proj.name)
			proj.autoStart = False

	#打印线程回调
	def printCallback(self, args):
		name = args[0]
		output = args[1]
		proj:ProjData = manager.projs[name]
		if output == None:
			manager.stop(proj)
			return
		if proj.ctrl:
			proj.ctrl.show(output)
	
	#子窗口关闭回调
	def windowCloseCallback(self, window:QMdiSubWindow):
		name = window.windowTitle()
		window.deleteLater()
		if name not in manager.projs.keys(): return
		proj:ProjData = manager.projs[name]
		if proj.ctrl.window != window: return #不是一个窗口了
		manager.stop(proj)
		proj.ctrl.window = None

	#---------------------------------------------------------------
	#分发原文
	def distOrig(self, proj:ProjData):
		if len(proj.waitList) > 0: 
			print('项目还有尚未翻译的文件，本次不分发', proj.name)
			return
		for i in range(len(self.waitList)-1, -1, -1):
			name = self.waitList[i]
			if name in self.projsWaitList:
				#已在某个项目中
				continue
			path = os.path.join(self.origpath, name)
			proj.ctrl.copyFromManager(name, path)
			self.waitList.pop(i)
			self.projsWaitList.add(name)
			return
		print('管理器中没有待翻译的文件', proj.name)

	def checkWait(self):
		self.waitList.clear()
		#译文
		transList = self.getTransList()
		#原文
		for name in os.listdir(self.origpath):
			#添加wait
			if name not in transList:
				if name not in self.projsWaitList:
					self.waitList.insert(0, name)

	#---------------------------------------------------------------
	#检查所有项目译文
	def checkTrans(self):
		self.projsWaitList.clear()
		for name, proj in self.projs.items():
			#判断是否有需要复制的译文
			manager.receiveTrans(proj)
			self.projsWaitList.update(proj.waitList)

	#复制译文
	def receiveTrans(self, proj:ProjData):
		proj.ctrl.checkFiles()
		proj.ctrl.copyToManager(self.transpath, self.getTransList())

	def getTransList(self):
		return os.listdir(self.transpath)

#---------------------------------------------------------------
manager = TransManager()

#---------------------------------------------------------------
