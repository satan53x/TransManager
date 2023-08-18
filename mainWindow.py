import math
from time import sleep
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QSettings, Qt, QTimer, QSize
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox
from ui_transManager import Ui_TransManager
from manager import manager
from common	import initValue
from project import ProjCtrl, ProjData

class MainWindow(QMainWindow, Ui_TransManager):
	app = None

	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		self.setupUi(self)
		#self.toolTypeBox.setView(QListView())
		self.workpathButton.clicked.connect(self.chooseWorkpath)
		self.toolpathButton.clicked.connect(self.chooseToolpath)
		self.refreshButton.clicked.connect(self.refreshProjs)
		self.startAllButton.clicked.connect(self.startAll)
		self.createButton.clicked.connect(self.createProj)
		self.startButton.clicked.connect(self.startSelect)
		#self.printMdi.subWindowActivated.connect(self.subWindowActivated)
		self.newApiButton.clicked.connect(self.showApi)
		self.saveApiButton.clicked.connect(self.saveApi)
		self.clearProjsButton.clicked.connect(self.clearProjsFile)
		#计时器
		self.timer = QTimer()
		self.timer.timeout.connect(self.handleTimer)
		self.timerTips = set()

	def resizeEvent(self, event):
		if not self.timer.isActive():
			self.timerTips.add('windowSize')
			self.timer.start(3000)
		self.resizeUI()

	def handleTimer(self):
		while len(self.timerTips) > 0:
			tip = self.timerTips.pop()
			if tip == 'windowSize':
				self.mainConfig.setValue('windowSize', self.size())
			elif tip == 'saveConfig':
				self.saveConfig()
		self.timer.stop()
	
	def beforeShow(self):
		self.mainConfig = QSettings('config.ini', QSettings.IniFormat)
		self.mainConfig.setIniCodec('utf-8')
		#manager.mainConfig = self.mainConfig
		manager.mainWindow = self 
		# 窗口大小
		windowSize = initValue(self.mainConfig, 'windowSize', None)
		if windowSize: self.resize(windowSize)
		#目录
		manager.workpath = initValue(self.mainConfig, 'workpath', '')
		self.workpathEdit.setText(manager.workpath)
		manager.tooltype = int(initValue(self.mainConfig, 'tooltype', 0))
		self.tooltypeBox.setCurrentIndex(manager.tooltype)
		manager.preCmd = initValue(self.mainConfig, 'preCmd', '')
		self.preCmdEdit.setText(manager.preCmd)
		manager.printEncode = initValue(self.mainConfig, 'printEncode', 'GBK')
		self.printEncodeEdit.setText(manager.printEncode)
		#工作线程
		# self.workThread = WorkThread()
		# self.workThread.executor = self
		# self.workThread.doneSig.connect(self.workDone)
		self.resizeUI()
	
	def resizeUI(self):
		#UI
		width = self.size().width()
		self.projTable.setColumnWidth(2, int(width*0.7))
		self.apiTable.setColumnWidth(1, int(width*0.7))
		self.apiTable.setColumnWidth(2, int(width*0.2))
	
	def afterShow(self):
		#刷新
		self.refreshApi()
		manager.init()
		self.refreshProjs()

	#---------------------------------------------------------------
	#刷新
	def refreshProjs(self):
		if manager.workpath == '':
			self.statusbar.showMessage('没有选择工作目录')
			self.mainTabs.setCurrentIndex(3)
			return
		self.statusbar.showMessage('')
		manager.preCmd = self.preCmdEdit.text()
		manager.refreshProjs()
		self.projTable.setRowCount(0)
		for name, proj in manager.projs.items():
			#读取缓存
			if proj.apiSeq == '':
				seq = initValue(self.mainConfig, f'{proj.name}/apiSeq', None)
				if seq: proj.apiSeq = seq
			#显示到项目列表
			proj.ctrl.checkFiles()
			proj.ctrl.showProj(self.projTable)
			if proj.process:
				proj.ctrl.showColor(QColor(84, 179, 69))

	#新建
	def createProj(self):
		nameList = [name for name, proj in manager.projs.items()]
		for i in range(1, 1000): #最大项目数
			name = f'p{i}'
			if name not in nameList:
				manager.createProj(name)
				break
		self.refreshProjs()

	#启动所有项目
	def startAll(self):
		manager.printEncode = self.printEncodeEdit.text()
		#self.workThread.set(saveConfig, None)
		self.saveConfig()
		self.stopAll()
		#检查译文
		manager.checkTrans()
		manager.checkWait()
		for name, proj in manager.projs.items():
			self.startProj(name)
		if len(manager.projs) > 0:
			self.mainTabs.setCurrentIndex(1)

	#启动项目
	def startProj(self, name):
		proj:ProjData = manager.projs[name]
		if proj.process:
			print('项目正在运行', name)
			return
		if proj.autoStart:
			print('自动重启', name)
			manager.checkTrans()
			manager.checkWait()
		#尝试分发文件
		ret = manager.distOrig(proj)
		if ret == False: return
		print('启动项目', name)
		if proj.ctrl.window:
			#self.printMdi.removeSubWindow(proj.ctrl.window)
			#proj.ctrl.window = None
			window = proj.ctrl.window
		else:
			window = proj.ctrl.createSub(manager.windowCloseCallback)
			#window.hide.connect(self.subWindowClose)
			#重设子窗口大小
			sw = math.ceil(pow(len(manager.projs), 0.5))
			sw = min(sw, 3)
			sh = math.ceil(len(manager.projs) / sw)
			sh = min(sh, 2)
			width = self.projTable.size().width() // sw
			height = self.projTable.size().height() // sh
			window.resize(QSize(width, height))
			self.printMdi.addSubWindow(window)
			window.show()
		self.printMdi.setActiveSubWindow(window)
		#修改项目配置文件
		self.applyApi(proj)
		#启动
		manager.start(proj)
		#保存配置
		self.mainConfig.setValue(f'{proj.name}/apiSeq', proj.apiSeq)

	def stopAll(self):
		self.printMdi.closeAllSubWindows() #子窗口close信号会通知
		# for name, proj in manager.projs.items():
		# 	manager.stop(proj)
		# 	proj.ctrl.window = None
	
	#启动选中项目
	def startSelect(self):
		rowSet = set()
		for item in self.projTable.selectedItems():
			#print(item.row())
			rowSet.add(item.row())
		lst = list(manager.projs.keys())
		for row in rowSet:
			name = lst[row]
			self.startProj(name)
			
	#---------------------------------------------------------------
	#刷新API
	def refreshApi(self):
		self.mainConfig.beginGroup('API')
		seqList = self.mainConfig.childKeys()
		self.apiTable.setRowCount(0)
		for row in range(len(seqList)):
			seq = seqList[row]
			key, url = self.mainConfig.value(seq)
			self.showApi([seq, key, url])
		self.mainConfig.endGroup()
	
	#显示API
	def showApi(self, data = None):
		table = self.apiTable
		row = table.rowCount()
		table.insertRow(row)
		seq = data[0] if data else ''
		key = data[1] if data else ''
		url = data[2] if data else ''
		item = QTableWidgetItem(f'{seq}')
		item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
		item.setCheckState(True)
		table.setItem(row, 0, item)
		item = QTableWidgetItem(f'{key}')
		table.setItem(row, 1, item)
		item = QTableWidgetItem(f'{url}')
		table.setItem(row, 2, item)
	
	#缓存API
	def saveApi(self):
		self.mainConfig.remove('API')
		self.mainConfig.beginGroup('API')
		table = self.apiTable
		count = 0
		for row in range(table.rowCount()):
			seq = table.item(row, 0).text()
			key = table.item(row, 1).text()
			url = table.item(row, 2).text()
			if seq == '' or key == '': 
				continue
			self.mainConfig.setValue(seq, [key, url])
			count += 1
		self.mainConfig.endGroup()
		self.statusbar.showMessage(f'API保存成功：{count}项')

	#获取API
	def getApi(self, target):
		table = self.apiTable
		for row in range(table.rowCount()):
			seq = table.item(row, 0).text()
			if seq != target: continue
			key = table.item(row, 1).text()
			url = table.item(row, 2).text()
			return key, url
		return '', ''

	#应用API到配置
	def applyApi(self, proj):
		table = self.projTable
		for row in range(table.rowCount()):
			name = table.item(row, 0).text()
			if name != proj.name: continue
			proj.apiSeq = table.item(row, 2).text()
			if proj.apiSeq == '': 
				print('API为空, 不修改', name)
				continue
			#获取key和url
			proj.apiKey, proj.apiUrl = self.getApi(proj.apiSeq)
			proj.numOnce = int(table.item(row, 3).text())
			proj.ctrl.writeConfig()
	#---------------------------------------------------------------
	#选择工作目录
	def chooseWorkpath(self):
		dirpath = self.mainConfig.value('workpath')
		dirpath = QFileDialog.getExistingDirectory(None, self.workpathButton.text(), dirpath)
		if dirpath != '':
			manager.workpath = dirpath
			self.workpathEdit.setText(dirpath)
			self.mainConfig.setValue('workpath', dirpath)
			self.stopAll()
			manager.init()
			self.refreshProjs()
	
	#选择工具目录
	def chooseToolpath(self):
		dirpath, _ = QFileDialog.getOpenFileName(None, self.toolpathButton.text(), '.')
		if dirpath != '':
			manager.tooltype = self.tooltypeBox.currentIndex()
			preCmd = manager.setPreCmd(dirpath)
			self.preCmdEdit.setText(preCmd)
			self.mainConfig.setValue('preCmd', preCmd)
	
	def clearProjsFile(self):
		result = QMessageBox.question(self, '警告', \
				'危险操作，确定清理所有项目的文件吗？',\
				QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.No: return
		for name, proj in manager.projs.items():
			if proj.process:
				print('项目正在运行无法清理', name)
				continue
			proj.ctrl.clearAllFile()
		print('清理完成')
		self.refreshProjs()

	#---------------------------------------------------------------
	def workDone(self, callback):
		callback(self)
	
	def saveConfig(self):
		self.mainConfig.setValue('printEncode', manager.printEncode)

