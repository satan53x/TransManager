import os

#创建文件夹
def createFolder(dirpath, nameList):
	for name in nameList:
		path = os.path.join(dirpath, name)
		if not os.path.exists(path):
			os.makedirs(path)

#设置初始值
def initValue(setting, name, v):
	if setting.value(name) == None:
		if v != None:
			setting.setValue(name, v)
			print('New Config', name, v)
	else:
		v = setting.value(name)
		#print('Load Config', name, v)
	return v

def clearFolder(dirpath):
	for name in os.listdir(dirpath):
		path = os.path.join(dirpath, name)
		try:
			if os.path.isfile(path):
				os.unlink(path)  # 删除文件
				print('删除文件：', name)
			# elif os.path.isdir(path):
			# 	os.rmdir(path)   # 删除子文件夹
		except Exception as e:
			print(f"Error deleting {path}: {e}")