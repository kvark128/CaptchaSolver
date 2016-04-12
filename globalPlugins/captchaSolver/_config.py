import globalVars
import pickle
import os.path
import wx
import gui
import addonHandler

addonHandler.initTranslation()
fileConfigPath = os.path.join(globalVars.appArgs.configPath, 'captchaSolverSettings.pickle')
defaultConf = {
	'key': '',
	'regsense': False,
}

def saveConfig():
	try:
		fileConfig = open(fileConfigPath, 'wb')
		pickle.dump(conf, fileConfig)
		fileConfig.close()
	except (IOError, OSError), e:
		gui.messageBox(e.strerror, _('Error saving settings'), style=wx.OK | wx.ICON_ERROR)

def loadConfig():
	try:
		fileConfig = open(fileConfigPath, 'rb')
		conf = pickle.load(fileConfig)
		fileConfig.close()
	except:
		conf = defaultConf
	else:
		for i in defaultConf:
			if i not in conf:
				conf[i] = defaultConf[i]
	return conf

conf = loadConfig()
