import threading
import time
import globalPluginHandler
import wx
import scriptHandler
import addonHandler
import ui
import api
import speech
import controlTypes
from error import errorHandler
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

	def sendCaptcha(self, **kwargs):
		kwargs['soft_id'] = 1665
		kwargs['regsense'] = int(_config.conf['regsense'])
		kwargs['language'] = _config.conf['language']
		response = requestAPI(**kwargs)
		speech.cancelSpeech()
		if not response.startswith('OK|'):
			errorHandler(response)
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
			errorHandler(status)

	def balance(self):
		balance = requestAPI(action='getbalance')
		try:
			ui.message(_('Balance: {:.2f}').format(float(balance)))
		except ValueError:
			errorHandler(balance)

	def terminate(self):
		self._running = False

	def script_startRecognition(self, gesture):
		obj = api.getNavigatorObject()
		if controlTypes.STATE_OFFSCREEN in obj.states:
			errorHandler('OFF_SCREEN')
			return

		try:
			x, y, width, height = obj.location
		except:
			errorHandler('CAPTCHA_HAS_NO_LOCATION')
			return

		if _config.conf['sizeReport'] and scriptHandler.getLastScriptRepeatCount() != 1:
			ui.message(_('Size: {0} X {1} pixels').format(width, height))
			return

		bmp = wx.EmptyBitmap(width, height)
		mem = wx.MemoryDC(bmp)
		mem.Blit(0, 0, width, height, wx.ScreenDC(), x, y)
		wx.CallAfter(interface.getInstruction, self.sendCaptcha, image=bmp.ConvertToImage())
	script_startRecognition.__doc__ = _('Starts the recognition process')

	def script_getBalance(self, gesture):
		threading.Thread(target=self.balance).start()
	script_getBalance.__doc__ = _('Report account balance')

	def script_showSettingsDialog(self, gesture):
		interface.showSettingsDialog()
	script_showSettingsDialog.__doc__ = _('Show the settings dialog')
