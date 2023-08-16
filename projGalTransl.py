import os
import shutil
from project import ProjCtrl
import yaml

OrigDirName = 'json_jp'
TransDirName = 'json_cn'

class ProjTrans(ProjCtrl):

	def checkFile(self, dirName, fileName):
		if dirName == 'orig':
			dirName = OrigDirName
		elif dirName == 'trans':
			dirName = TransDirName
		path = os.path.join(self.proj.path, dirName, fileName)
		if os.path.isfile(path):
			return True, path
		else:
			return False, path
		
	def checkFiles(self):
		self.proj.origList.clear()
		self.proj.transList.clear()
		self.proj.waitList.clear()
		origPath = os.path.join(self.proj.path, OrigDirName)
		transPath = os.path.join(self.proj.path, TransDirName)
		#译文
		if os.path.isdir(transPath):
			for name in os.listdir(transPath):
				self.proj.transList.append(name)
		#原文
		if os.path.isdir(origPath):
			for name in os.listdir(origPath):
				self.proj.origList.append(name)
				#添加wait
				if name not in self.proj.transList:
					self.proj.waitList.append(name)

	#输出译文
	def copyToManager(self, transDir, transList):
		for name in self.proj.transList:
			if name in transList: continue #已存在
			src = os.path.join(self.proj.path, TransDirName, name)
			dst = os.path.join(transDir, name)
			shutil.copy(src, dst)
			print(f'从项目{self.proj.name}复制译文 {name}')
	
	#导入原文
	def copyFromManager(self, name, src):
		dst = os.path.join(self.proj.path, OrigDirName, name)
		if os.path.isfile(dst):
			print(f'>> {self.proj.name}项目已存在{name}，请检查文件是否一致')
			return False
		shutil.copy(src, dst)
		print(f'向项目{self.proj.name}导入原文 {name}')
		self.proj.origList.append(name)
		self.proj.waitList.append(name)
		return True

#---------------------------------------------------------------
class ProjGalTransl(ProjTrans):
	configContent = None

	def getPreCmd(toolpath):
		preCmd = 'python -u ' + toolpath + r' {projpath} gpt35'
		return preCmd

	def checkFiles(self):
		super().checkFiles()
		self.readConfig()

	def readConfig(self):
		if self.configContent: return
		configPath = os.path.join(self.proj.path, 'config.yaml')
		file = open(configPath, 'r', encoding='utf-8')
		self.configContent = yaml.safe_load(file)
		file.close()
		self.proj.numOnce = self.configContent['common']['gpt.numPerRequestTranslate']

	def writeConfig(self, typeName='GPT35'):
		tokens = self.configContent['backendSpecific'][typeName]['tokens']
		tokens.clear()
		tokens.append({
			'token': self.proj.apiKey, 
			'endpoint': self.proj.apiUrl
		})
		self.configContent['common']['gpt.numPerRequestTranslate'] = self.proj.numOnce
		#写入
		configPath = os.path.join(self.proj.path, 'config.yaml')
		file = open(configPath, 'w', encoding='utf-8')
		yaml.dump(self.configContent, file, encoding='utf-8', allow_unicode=True)
		file.close()

	def show(self, output):
		super().show(output)
		lst = output.splitlines()
		if len(lst) > 0 and lst[-1].startswith('Done.'):
			self.proj.autoStart = True
			return
		if '200 / day' in output:
			self.proj.dayLimit = True