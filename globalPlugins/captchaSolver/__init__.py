import io
import threading
import time
import urllib
import globalPluginHandler
import wx
import addonHandler
import ui
import api
from logHandler import log
from responses import responses
import interface
from rucaptcha import requestAPI
import _config

addonHandler.initTranslation()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _('Captcha Solver')
	_running = True

	def __init__(self):
		super(GlobalPlugin, self).__init__()
		interface.createMenuItem()

	def sendCaptcha(self, captcha):
		response = requestAPI(captcha.getvalue(), regsense=int(_config.conf['regsense']), soft_id=1665)
		if not response.startswith('OK|'):
			self.errorHandler(response)
			return

		ui.message(_('Captcha successfully sent to the recognition. You will be notified when the result will be ready'))
		time.sleep(3)
		while self._running:
			status = requestAPI(action='get', id=response[3:])
			if (status != 'CAPCHA_NOT_READY') and self._running:
				break
			time.sleep(2)
		else: return

		if status.startswith('OK|'):
			api.copyToClip(status.decode('utf-8')[3:])
			ui.message(_('Captcha solved successfully! The result copied to the clipboard'))
		else:
			self.errorHandler(status)

	def balance(self):
		balance = requestAPI(action='getbalance')
		try:
			ui.message(_('Balance: {balance:.2f} rubles').format(balance=float(balance)))
		except ValueError:
			self.errorHandler(balance)

	def errorHandler(self, msg):
		text = responses.get(msg)
		if text is None:
			text = _('Error: {}').format(msg)
		ui.message(text)
		log.error(msg)

	def terminate(self):
		self._running = False

	def script_startRecognition(self, gesture):
		obj = api.getNavigatorObject()
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
		interface.showSettingsDialog()
	script_showSettingsDialog.__doc__ = _('Show the settings dialog')
