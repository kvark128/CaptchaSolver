import wx
import threading
import addonHandler
import gui
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

		self.sizeReport = wx.CheckBox(self, label=_('Size image report'))
		self.sizeReport.SetValue(_config.conf['sizeReport'])
		sizer.Add(self.sizeReport)

		self.textInstruction = wx.CheckBox(self, label=_('Send text instruction'))
		self.textInstruction.SetValue(_config.conf['textInstruction'])
		sizer.Add(self.textInstruction)

		label = wx.StaticText(self, label=_('API key:'))
		self.key = wx.TextCtrl(self, value=_config.conf['key'].decode('utf-8'))
		sizer.Add(gui.guiHelper.associateElements(label, self.key))

	def postInit(self):
		self.regsense.SetFocus()

	def onOk(self, event):
		super(SettingsDialog, self).onOk(event)
		_config.conf['regsense'] = self.regsense.Value
		_config.conf['https'] = self.https.Value
		_config.conf['sizeReport'] = self.sizeReport.Value
		_config.conf['textInstruction'] = self.textInstruction.Value
		_config.conf['key'] = self.key.Value.encode('utf-8')
		_config.saveConfig()

def createMenuItem():
	prefsMenu = gui.mainFrame.sysTrayIcon.menu.GetMenuItems()[1].GetSubMenu()
	captchaSolverSettingsItem = prefsMenu.Append(wx.ID_ANY, _('Captcha Solver Settings...'))
	gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, showSettingsDialog, captchaSolverSettingsItem)

def showSettingsDialog(evt=None):
	gui.mainFrame._popupSettingsDialog(SettingsDialog)

def getInstruction(callback, **kwargs):
	if _config.conf['textInstruction']:
		dlg = wx.TextEntryDialog(gui.mainFrame, _('Text instruction:'), _('title'))
		gui.mainFrame.prePopup()
		status = dlg.ShowModal()
		text = dlg.GetValue()
		gui.mainFrame.postPopup()
		dlg.Destroy()
		if status != wx.ID_OK:
			return
		kwargs['textinstructions'] = text.encode('utf-8')
	threading.Thread(target=callback, kwargs=kwargs).start()
