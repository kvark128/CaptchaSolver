import globalVars
import cPickle
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
	conf.update(cPickle.load(fileConfig))
	fileConfig.close()
except:
	pass

def saveConfig():
	try:
		fileConfig = open(fileConfigPath, 'wb')
		cPickle.dump(conf, fileConfig, cPickle.HIGHEST_PROTOCOL)
		fileConfig.close()
	except (IOError, OSError), e:
		gui.messageBox(e.strerror, _('Error saving settings'), style=wx.OK | wx.ICON_ERROR)
