import threading
import os
import json
import base64
import io
import httplib
import time
from urllib import urlencode
import globalPluginHandler
import wx
import gui
from logHandler import log
import scriptHandler
import addonHandler
import queueHandler
import ui
import globalVars
import api
import speech
import controlTypes
import _config

addonHandler.initTranslation()

ERRORS = {
	'NVDA_SECURE_DESKTOP': _('Action cannot be performed because NVDA running on secure desktop'),
	'OFF_SCREEN': _('Captcha off screen'),
	'CAPTCHA_HAS_NO_LOCATION': _('Captcha has no location'),
	'ERROR_CONNECTING_TO_SERVER': _('Error connecting to server. Please check your Internet connection'),
	'ERROR_WRONG_USER_KEY': _('API key is not specified'),
	'ERROR_KEY_DOES_NOT_EXIST': _('Used a non-existent API key'),
	'ERROR_ZERO_BALANCE': _('The balance of your account is zero'),
	'ERROR_NO_SLOT_AVAILABLE': _('The current recognition rate is higher than the maximum set in the settings of Your account. Either on the server queue builds up and employees do not have time to disassemble it, repeat the sending captcha after 5 seconds'),
	'ERROR_ZERO_CAPTCHA_FILESIZE': _('Size of the captcha is less than 100 bytes'),
	'ERROR_TOO_BIG_CAPTCHA_FILESIZE': _('Size of the captcha more than 100 KB'),
	'ERROR_IP_NOT_ALLOWED': _('In Your account you have configured restrictions based on IP from which you can make requests. And the IP from which the request is not included in the allowed list'),
	'IP_BANNED': _('IP address from which the request is blocked because of frequent requests with various incorrect API keys. The lock is released in an hour'),
	'ERROR_CAPTCHA_UNSOLVABLE': _('Captcha could not solve 3 different employee. Money for this image come back to balance'),
	'ERROR_BAD_DUPLICATES': _('The error appears when 100 percent recognition. Has been used the maximum number of attempts, but the required number of identical answers has not been received'),
	'ERROR_CAPTCHAIMAGE_BLOCKED': _('This captcha can not be recognized'),
}

class SettingsDialog(gui.SettingsDialog):
	title = _('Captcha Solver Settings')

	def makeSettings(self, sizer):
		settingsSizerHelper = gui.guiHelper.BoxSizerHelper(self, sizer=sizer)

		self.graphicOnly = wx.CheckBox(self, label=_('Recognize only &graphic objects'))
		self.graphicOnly.SetValue(_config.conf['graphicOnly'])
		settingsSizerHelper.addItem(self.graphicOnly)

		self.regsense = wx.CheckBox(self, label=_('&Case sensitive recognition'))
		self.regsense.SetValue(_config.conf['regsense'])
		settingsSizerHelper.addItem(self.regsense)

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
		self.graphicOnly.SetFocus()

	def onOk(self, event):
		_config.conf['graphicOnly'] = self.graphicOnly.Value
		_config.conf['regsense'] = self.regsense.Value
		_config.conf['sizeReport'] = self.sizeReport.Value
		_config.conf['textInstruction'] = self.textInstruction.Value
		_config.conf['language'] = self.language.GetSelection()
		_config.conf['key'] = self.key.Value
		_config.saveConfig()
		super(SettingsDialog, self).onOk(event)

class RucaptchaRequest(threading.Thread):

	def __init__(self, callback, **kwargs):
		super(RucaptchaRequest, self).__init__()
		self.__callback = callback
		self.__kwargs = kwargs
		self.__host = 'rucaptcha.com'
		self.__connection = httplib.HTTPSConnection(self.__host, timeout=20)
		self.daemon = True
		self.start()

	def run(self):
		status, request = self._request(**self.__kwargs)
		self.__connection.close()
		queueHandler.queueFunction(queueHandler.eventQueue, self.__callback, status=status, request=request)

	def _request(self, **kwargs):
		kwargs['json'] = 1
		kwargs['key'] = _config.conf['key'].encode('utf-8')

		if 'body' not in kwargs:
			path = '/res.php?' + urlencode(kwargs)
			return self._HTTPRequest('GET', path, None)

		kwargs['soft_id'] = 1665
		kwargs['regsense'] = int(_config.conf['regsense'])
		kwargs['language'] = _config.conf['language']
		kwargs['method'] = 'base64'
		kwargs['body'] = base64.b64encode(kwargs['body'])

		status, request = self._HTTPRequest('POST', '/in.php', urlencode(kwargs))

		if not status:
			return status, request

		queueHandler.queueFunction(queueHandler.eventQueue, speech.cancelSpeech)
		queueHandler.queueFunction(queueHandler.eventQueue, ui.message, _('Captcha successfully sent to the recognition. You will be notified when the result will be ready'))

		while True:
			time.sleep(2)
			status, result = self._request(action='get', id=request)
			if status or result != 'CAPCHA_NOT_READY':
				return status, result

	def _HTTPRequest(self, method, path, body):
		headers = {'Host': self.__host}
		if body:
			headers['Content-Type'] = 'application/x-www-form-urlencoded'

		try:
			self.__connection.request(method, path, body, headers)
			response = self.__connection.getresponse()
		except (httplib.socket.gaierror, httplib.ssl.SSLError):
			return False, 'ERROR_CONNECTING_TO_SERVER'

		if response.status != httplib.OK:
			return False, '{} {}'.format(response.status, response.reason)

		try:
			responseDict = json.load(response)
		except Exception as e:
			return False, e

		status = responseDict.get('status', 0)
		request = responseDict.get('request', None)
		return bool(status), request

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _('Captcha Solver')

	def __init__(self):
		super(GlobalPlugin, self).__init__()
		if globalVars.appArgs.secure:
			return
		self.createSubmenu()

	def createSubmenu(self):
		menu_tools = gui.mainFrame.sysTrayIcon.menu.FindItemByPosition(1).GetSubMenu()
		menu_CaptchaSolver = wx.Menu()
		item = menu_CaptchaSolver.Append(wx.ID_ANY, _('Settings...'))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda evt: gui.mainFrame._popupSettingsDialog(SettingsDialog), item)
		item = menu_CaptchaSolver.Append(wx.ID_ANY, _('Account balance...'))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda evt: RucaptchaRequest(self.balanceDialog, action='getbalance'), item)
		item = menu_CaptchaSolver.Append(wx.ID_ANY, _('Profile on rucaptcha.com'))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda evt: os.startfile('https://rucaptcha.com/auth/login'), item)
		item = menu_CaptchaSolver.Append(wx.ID_ANY, _('Addon webpage'))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda evt: os.startfile('https://github.com/kvark128/captchaSolver'), item)
		menu_tools.AppendMenu(wx.ID_ANY, _('Captcha Solver'), menu_CaptchaSolver)

	def getErrorDescription(self, error):
		text = ERRORS.get(error)
		if not isinstance(text, basestring):
			text = _('Error: {}').format(error)
		log.error(error)
		return text

	def balanceDialog(self, status, request):
		if status:
			gui.messageBox(_('{:.2f} rubles').format(float(request)), _('Your account balance'))
		else:
			gui.messageBox(self.getErrorDescription(request), _('Error getting balance'), style=wx.OK | wx.ICON_ERROR)

	def captchaHandler(self, status, request):
		if not status:
			ui.message(self.getErrorDescription(request))
			return

		api.copyToClip(request)
		ui.message(_('Captcha solved successfully! The result copied to the clipboard'))

	def balanceHandler(self, status, request):
		if not status:
			ui.message(self.getErrorDescription(request))
			return

		ui.message(_('Balance: {:.2f}').format(float(request)))

	def _creator(self, **kwargs):
		if _config.conf['textInstruction']:
			dlg = wx.TextEntryDialog(gui.mainFrame, _('Instruction text (maximum 140 characters):'), _('Sending text instruction'))
			gui.mainFrame.prePopup()
			status = dlg.ShowModal()
			gui.mainFrame.postPopup()
			textInstruction = dlg.GetValue()
			dlg.Destroy()
			if status != wx.ID_OK: return
			kwargs['textinstructions'] = textInstruction[:140].encode('utf-8')
		RucaptchaRequest(self.captchaHandler, **kwargs)

	def script_startRecognition(self, gesture):
		if globalVars.appArgs.secure:
			ui.message(self.getErrorDescription('NVDA_SECURE_DESKTOP'))
			return

		obj = api.getNavigatorObject()

		if obj.role != controlTypes.ROLE_GRAPHIC and _config.conf['graphicOnly']:
			ui.message(_('This object is not a graphical element'))
			return

		if controlTypes.STATE_OFFSCREEN in obj.states:
			ui.message(self.getErrorDescription('OFF_SCREEN'))
			return

		try:
			x, y, width, height = obj.location
		except:
			ui.message(self.getErrorDescription('CAPTCHA_HAS_NO_LOCATION'))
			return

		if _config.conf['sizeReport'] and scriptHandler.getLastScriptRepeatCount() != 1:
			ui.message(_('Size: {0} X {1} pixels').format(width, height))
			return

		bmp = wx.EmptyBitmap(width, height)
		mem = wx.MemoryDC(bmp)
		mem.Blit(0, 0, width, height, wx.ScreenDC(), x, y)
		image = bmp.ConvertToImage()
		body = io.BytesIO()
		if wx.__version__ == '3.0.2.0': # Maintain compatibility with old version of WXPython
			image.SaveStream(body, wx.BITMAP_TYPE_PNG)
		else: # Used in WXPython 4.0
			image.SaveFile(body, wx.BITMAP_TYPE_PNG)

		wx.CallAfter(self._creator, body=body.getvalue())
	script_startRecognition.__doc__ = _('Starts the recognition process')

	def script_getBalance(self, gesture):
		if globalVars.appArgs.secure:
			ui.message(self.getErrorDescription('NVDA_SECURE_DESKTOP'))
			return

		RucaptchaRequest(self.balanceHandler, action='getbalance')
	script_getBalance.__doc__ = _('Report account balance')

	def script_showSettingsDialog(self, gesture):
		if globalVars.appArgs.secure:
			ui.message(self.getErrorDescription('NVDA_SECURE_DESKTOP'))
			return

		gui.mainFrame._popupSettingsDialog(SettingsDialog)
	script_showSettingsDialog.__doc__ = _('Show the settings dialog')
