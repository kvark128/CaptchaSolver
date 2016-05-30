# -*- coding: utf-8 -*-

import io
import httplib
import threading
import time
import urllib
import globalPluginHandler
import controlTypes
import tones
import wx
import gui
import addonHandler
import ui
import api
from logHandler import log
import _config

addonHandler.initTranslation()

class captchaSolverSettingsDialog(gui.SettingsDialog):
	title = _('Captcha Solver Settings')

	def makeSettings(self, sizer):
		self.regsense = wx.CheckBox(self, label=_('Case sensitive recognition'))
		self.regsense.SetValue(_config.conf['regsense'])
		sizer.Add(self.regsense)

		sizer.Add(wx.StaticText(self, label=_('API key:')))
		self.key = wx.TextCtrl(self, value=urllib.unquote(_config.conf['key']).decode('utf-8'))
		sizer.Add(self.key)

	def postInit(self):
		self.regsense.SetFocus()

	def onOk(self, event):
		super(captchaSolverSettingsDialog, self).onOk(event)
		_config.conf['regsense'] = self.regsense.Value
		_config.conf['key'] = urllib.quote(self.key.Value.encode('utf-8'))
		_config.saveConfig()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _('Captcha Solver')
	run = True
	responses = {
		'ERROR_WRONG_USER_KEY': _('API key is not specified'),
		'ERROR_KEY_DOES_NOT_EXIST': _('Used a non-existent API key'),
		'ERROR_ZERO_BALANCE': _('The balance of your account is zero'),
		'ERROR_NO_SLOT_AVAILABLE': _('The current recognition rate is higher than the maximum set in the settings of Your account. Either on the server queue builds up and employees do not have time to disassemble it, repeat the sending captcha after 5 seconds'),
		'ERROR_ZERO_CAPTCHA_FILESIZE': _('Size of the captcha is less than 100 bytes'),
		'ERROR_TOO_BIG_CAPTCHA_FILESIZE': _('Size of the captcha more than 100 KB'),
		'ERROR_IP_NOT_ALLOWED': _('In Your account you have configured restrictions based on IP from which you can make requests. And the IP from which the request is not included in the allowed list'),
		'IP_BANNED': _('IP address from which the request is blocked because of frequent requests with various incorrect API keys. The lock is released in an hour'),
		'ERROR_CAPTCHA_UNSOLVABLE': _('Captcha could not solve 3 different employee. Money for this image come back to balance'),
		'ERROR_BAD_DUPLICATES': _('The error appears when 100% recognition. Has been used the maximum number of attempts, but the required number of identical answers has not been received'),
	}

	def __init__(self):
		super(GlobalPlugin, self).__init__()
		self.prefsMenu = gui.mainFrame.sysTrayIcon.menu.GetMenuItems()[1].GetSubMenu()
		self.captchaSolverSettingsItem = self.prefsMenu.Append(wx.ID_ANY, _('Captcha Solver Settings...'))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU , lambda i: gui.mainFrame._popupSettingsDialog(captchaSolverSettingsDialog), self.captchaSolverSettingsItem)

	def sendCaptcha(self, captcha):
		body = '''------------bundary------
Content-Disposition: form-data; name="regsense"

{regsense}
------------bundary------
Content-Disposition: form-data; name="key"

{key}
------------bundary------
Content-Disposition: form-data; name="file"; filename="captcha.png"

{captcha}
------------bundary--------
'''.format(regsense=int(_config.conf['regsense']), key=_config.conf['key'], captcha=captcha.getvalue())

		headers = {'Content-Type': 'multipart/form-data; boundary=----------bundary------'}
		server = httplib.HTTPConnection('rucaptcha.com', timeout=10)
		try:
			server.request('POST', '/in.php', body, headers)
			response = server.getresponse().read()
		except httplib.socket.gaierror:
			tones.beep(100, 200)
			ui.message(_('Failed to send captcha. Please check your Internet connection'))
			return
		finally:
			server.close()

		if not response.startswith('OK|'):
			tones.beep(100, 200)
			ui.message(self.responses[response])
			return

		ui.message(_('Captcha successfully sent to the recognition. You will be notified when the result will be ready'))
		time.sleep(3)
		while self.run:
			try:
				status = urllib.urlopen('http://rucaptcha.com/res.php?key=%s&action=get&id=%s' % (_config.conf['key'], response[3:])).read()
			except:
				tones.beep(100, 200)
				ui.message(_('I can not get the recognition result. Please check your internet connection'))
				return
			if (status != 'CAPCHA_NOT_READY') and self.run: break
			time.sleep(3)
		else: return

		if status.startswith('OK|'):
			api.copyToClip(status.decode('utf-8')[3:])
			ui.message(_('Captcha solved successfully! The result copied to the clipboard'))
		elif status in self.responses:
			ui.message(self.responses[status])
		else:
			ui.message(_('Error: %s') % status.decode('utf-8'))
			log.error(status)

	def balance(self):
		try:
			balance = urllib.urlopen('http://rucaptcha.com/res.php?key=%s&action=getbalance' % _config.conf['key']).read()
		except IOError:
			tones.beep(100, 200)
			ui.message(_('Failed to get account balance. Please check your internet connection'))
			return
		if balance in self.responses:
			ui.message(self.responses[balance])
		else:
			ui.message(_('Your account balance: %s rubles') % balance[:-3])

	def terminate(self):
		self.run = False

	def script_startRecognition(self, gesture):
		obj = api.getNavigatorObject()
		if obj.role != controlTypes.ROLE_GRAPHIC:
			ui.message(_('This is not a captcha!'))
			return
		try:
			x, y, width, height = obj.location
		except:
			ui.message(_('Captcha has no location'))
			return
		bmp = wx.EmptyBitmap(width, height)
		mem = wx.MemoryDC(bmp)
		mem.Blit(0, 0, width, height, wx.ScreenDC(), x, y)
		image = bmp.ConvertToImage()
		captcha = io.BytesIO()
		image.SaveStream(captcha, wx.BITMAP_TYPE_PNG)
		threading.Thread(target=self.sendCaptcha, args=(captcha,)).start()
	script_startRecognition.__doc__ = _('To start solving captcha')

	def script_getBalance(self, gesture):
		threading.Thread(target=self.balance).start()
	script_getBalance.__doc__ = _('Report account balance')

	def script_showSettingsDialog(self, gesture):
		gui.mainFrame._popupSettingsDialog(captchaSolverSettingsDialog)
	script_showSettingsDialog.__doc__ = _('Show the settings dialog')
