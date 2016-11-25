import wx
from urllib import quote, unquote
import addonHandler
import gui
import gui.guiHelper
import _config

addonHandler.initTranslation()

class SettingsDialog(gui.SettingsDialog):
	title = _('Captcha Solver Settings')

	def makeSettings(self, sizer):
		self.regsense = wx.CheckBox(self, label=_('Case sensitive recognition'))
		self.regsense.SetValue(_config.conf['regsense'])
		sizer.Add(self.regsense)

		self.https = wx.CheckBox(self, label=_('Use HTTPS'))
		self.https.SetValue(_config.conf['https'])
		sizer.Add(self.https)

		self.key = wx.TextCtrl(self, value=unquote(_config.conf['key']).decode('utf-8'))
		sizerKey = gui.guiHelper.associateElements(wx.StaticText(self, label=_('API key:')), self.key)
		sizer.Add(sizerKey)

	def postInit(self):
		self.regsense.SetFocus()

	def onOk(self, event):
		super(SettingsDialog, self).onOk(event)
		_config.conf['regsense'] = self.regsense.Value
		_config.conf['https'] = self.https.Value
		_config.conf['key'] = quote(self.key.Value.encode('utf-8'))
		_config.saveConfig()
