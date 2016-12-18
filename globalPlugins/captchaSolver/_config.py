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
	'https': False,
}

try:
	with open(fileConfigPath, 'rb') as fileConfig:
		conf.update(cPickle.load(fileConfig))
except:
	pass

def saveConfig():
	try:
		with open(fileConfigPath, 'wb') as fileConfig:
			cPickle.dump(conf, fileConfig, cPickle.HIGHEST_PROTOCOL)
	except (IOError, OSError), e:
		gui.messageBox(e.strerror, _('Error saving settings'), style=wx.OK | wx.ICON_ERROR)
