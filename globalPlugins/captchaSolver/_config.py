import globalVars
import pickle
import os.path
import wx
import gui
import addonHandler

addonHandler.initTranslation()
fileConfigPath = os.path.join(globalVars.appArgs.configPath, 'captchaSolverSettings.pickle')
conf = {
	'key': '',
	'regsense': False,
}

try:
	fileConfig = open(fileConfigPath, 'rb')
	conf.update(pickle.load(fileConfig))
	fileConfig.close()
except:
	pass

def saveConfig():
	try:
		fileConfig = open(fileConfigPath, 'wb')
		pickle.dump(conf, fileConfig)
		fileConfig.close()
	except (IOError, OSError), e:
		gui.messageBox(e.strerror, _('Error saving settings'), style=wx.OK | wx.ICON_ERROR)
