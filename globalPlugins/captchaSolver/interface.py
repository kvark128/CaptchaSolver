import os
import wx
import threading
import addonHandler
import gui
import _config
from rucaptcha import requestAPI
from error import errorHandler

addonHandler.initTranslation()

class SettingsDialog(gui.SettingsDialog):
	title = _('Captcha Solver Settings')

	def makeSettings(self, sizer):
		settingsSizerHelper = gui.guiHelper.BoxSizerHelper(self, sizer=sizer)

		self.regsense = wx.CheckBox(self, label=_('&Case sensitive recognition'))
		self.regsense.SetValue(_config.conf['regsense'])
		settingsSizerHelper.addItem(self.regsense)

		self.https = wx.CheckBox(self, label=_('Use &HTTPS'))
		self.https.SetValue(_config.conf['https'])
		settingsSizerHelper.addItem(self.https)

		self.sizeReport = wx.CheckBox(self, label=_('Report image &size'))
		self.sizeReport.SetValue(_config.conf['sizeReport'])
		settingsSizerHelper.addItem(self.sizeReport)

		self.textInstruction = wx.CheckBox(self, label=_('Send &text instruction'))
		self.textInstruction.SetValue(_config.conf['textInstruction'])
		settingsSizerHelper.addItem(self.textInstruction)

		self.language = settingsSizerHelper.addLabeledControl(_('Image &language:'), wx.Choice, choices=[_('Undefined'), _('Only Cyrillic alphabet'), _('Only Latin alphabet')])
		self.language.SetSelection(_config.conf['language'])

		self.key = settingsSizerHelper.addLabeledControl(_('API &key:'), wx.TextCtrl, value=_config.conf['key'])

	def postInit(self):
		self.regsense.SetFocus()

	def onOk(self, event):
		super(SettingsDialog, self).onOk(event)
		_config.conf['regsense'] = self.regsense.Value
		_config.conf['https'] = self.https.Value
		_config.conf['sizeReport'] = self.sizeReport.Value
		_config.conf['textInstruction'] = self.textInstruction.Value
		_config.conf['language'] = self.language.GetSelection()
		_config.conf['key'] = self.key.Value
		_config.saveConfig()

def createSubmenu():
	menu_tools = gui.mainFrame.sysTrayIcon.menu.FindItemByPosition(1).GetSubMenu()
	menu_CaptchaSolver = wx.Menu()
	item = menu_CaptchaSolver.Append(wx.ID_ANY, _('Settings...'))
	gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, showSettingsDialog, item)
	item = menu_CaptchaSolver.Append(wx.ID_ANY, _('Account balance...'))
	gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, balanceDialog, item)
	item = menu_CaptchaSolver.Append(wx.ID_ANY, _('Profile on rucaptcha.com'))
	gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda evt: os.startfile('https://rucaptcha.com/auth/login'), item)
	item = menu_CaptchaSolver.Append(wx.ID_ANY, _('Donate to author CaptchaSolver'))
	gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda evt: os.startfile('https://money.yandex.ru/to/410012293543375'), item)
	item = menu_CaptchaSolver.Append(wx.ID_ANY, _('Addon webpage'))
	gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda evt: os.startfile('https://github.com/kvark128/captchaSolver'), item)
	menu_tools.AppendMenu(wx.ID_ANY, _('Captcha Solver'), menu_CaptchaSolver)

def balanceDialog(evt=None):
	balance = requestAPI(action='getbalance')
	try:
		text = _('{:.2f} rubles').format(float(balance))
	except ValueError:
		text = errorHandler(balance, True)
	gui.messageBox(text, _('Your account balance'))

def showSettingsDialog(evt=None):
	gui.mainFrame._popupSettingsDialog(SettingsDialog)

def getInstruction(callback, **kwargs):
	if _config.conf['textInstruction']:
		dlg = wx.TextEntryDialog(gui.mainFrame, _('Instruction text (maximum 140 characters):'), _('Sending text instruction'))
		gui.mainFrame.prePopup()
		status = dlg.ShowModal()
		gui.mainFrame.postPopup()
		textInstruction = dlg.GetValue()
		dlg.Destroy()
		if status != wx.ID_OK: return
		kwargs['textinstructions'] = textInstruction[:140].encode('utf-8')
	threading.Thread(target=callback, kwargs=kwargs).start()
