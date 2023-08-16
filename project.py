from time import sleep
from PyQt5.QtWidgets import QMdiSubWindow, QTextBrowser, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from thread import PrintThread



#---------------------------------------------------------------
class ProjCtrl:
	#proj = None #在init里新建以便加上类型说明
	window = None
	preCmd = ''
	tableItem:QTableWidgetItem = None

	def __init__(self, proj=None):
		self.proj:ProjData = proj

	def createSub(self, callback):
		self.window = MyMdiSubWindow()
		self.window.closeSig.connect(callback)
		self.window.setWidget(QTextBrowser())
		self.window.setWindowTitle(self.proj.name)
		return self.window

	def show(self, output):
		if not self.window: return
		textBrowser = self.window.widget()
		if textBrowser:
			text = textBrowser.toPlainText()
			if len(text) > 5000:
				text = text[2000:]
				textBrowser.setPlainText(text)
			textBrowser.moveCursor(textBrowser.textCursor().End)
			textBrowser.insertPlainText(output)

	def getCmd(self):
		command = self.preCmd.format(projpath=self.proj.path)
		return command
	
	def showProj(self, table:QTableWidget):
		row = table.rowCount()
		table.insertRow(row)
		item = QTableWidgetItem(self.proj.name)
		item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
		table.setItem(row, 0, item)
		self.tableItem = item #缓存Item
		count = len(self.proj.waitList)
		item = QTableWidgetItem(f'{count}')
		item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
		table.setItem(row, 1, item)
		item = QTableWidgetItem(self.proj.apiSeq)
		table.setItem(row, 2, item)
		item = QTableWidgetItem(f'{self.proj.numOnce}')
		table.setItem(row, 3, item)

	def showColor(self, color):
		self.tableItem.setBackground(color)

	def checkFiles():
		pass

#---------------------------------------------------------------
class ProjAny(ProjCtrl):
	def getPreCmd(toolpath):
		preCmd = toolpath + r' {projpath}'
		return preCmd

#---------------------------------------------------------------
class ProjData:
	def __init__(self, name, path):
		self.name = name
		self.path = path
		self.process = None
		self.ctrl:ProjCtrl = None
		self.printThread:PrintThread = None
		self.origList = []
		self.transList = []
		self.waitList = []
		self.apiSeq = ''
		self.apiKey = ''
		self.apiUrl = ''
		self.numOnce = 9
		self.autoStart = False

	#启动打印读取线程
	def startThread(self, callback):
		if self.printThread == None:
			self.printThread = PrintThread(self.name)
			self.printThread.printSig.connect(callback)
		self.printThread.mutex.lock()
		if self.printThread.state == 0:
			self.printThread.state = 1
		self.printThread.mutex.unlock()
		self.printThread.start()


#---------------------------------------------------------------
class MyMdiSubWindow(QMdiSubWindow):
	closeSig = pyqtSignal(object)

	def closeEvent(self, event):
		# 子窗口被关闭时触发
		#print(f"Sub window '{self.windowTitle()}' is closed.")
		self.closeSig.emit(self)
		super().closeEvent(event)
		#self.deleteLater()