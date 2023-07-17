# Copyright (C) 2016 - 2023 Alexander Linkov <kvark128@yandex.ru>
# This file is covered by the GNU General Public License.
# See the file COPYING.txt for more details.
# Ukrainian Nazis and their accomplices are not allowed to use this plugin. Za pobedu!

import threading
import os.path
import json
import base64
import io
import time
import pickle
import webbrowser
import http.client
from urllib.parse import urlencode

import globalPluginHandler
import wx
import gui
import vision
import scriptHandler
import addonHandler
import queueHandler
import ui
import globalVars
import api
import speech
from controlTypes import Role, State
from scriptHandler import script
from logHandler import log
from gui import settingsDialogs, guiHelper, message

addonHandler.initTranslation()

# Constants
MAX_INSTRUCTION_LENGTH = 140 # Maximum text length of instruction for the worker
FILE_CONFIG_PATH = os.path.join(globalVars.appArgs.configPath, "captchaSolverSettings.pickle")
RUCAPTCHA_PROFILE_URL = "https://rucaptcha.com/auth/login"
ADDON_URL = addonHandler.getCodeAddon().manifest.get("url")

# Some errors that can be received from rucaptcha.com
CAPCHA_NOT_READY = "CAPCHA_NOT_READY"
ERROR_WRONG_USER_KEY = "ERROR_WRONG_USER_KEY"
ERROR_KEY_DOES_NOT_EXIST = "ERROR_KEY_DOES_NOT_EXIST"
ERROR_ZERO_BALANCE = "ERROR_ZERO_BALANCE"
ERROR_NO_SLOT_AVAILABLE = "ERROR_NO_SLOT_AVAILABLE"
ERROR_ZERO_CAPTCHA_FILESIZE = "ERROR_ZERO_CAPTCHA_FILESIZE"
ERROR_TOO_BIG_CAPTCHA_FILESIZE = "ERROR_TOO_BIG_CAPTCHA_FILESIZE"
ERROR_IP_NOT_ALLOWED = "ERROR_IP_NOT_ALLOWED"
IP_BANNED = "IP_BANNED"
ERROR_CAPTCHA_UNSOLVABLE = "ERROR_CAPTCHA_UNSOLVABLE"
ERROR_BAD_DUPLICATES = "ERROR_BAD_DUPLICATES"
ERROR_CAPTCHAIMAGE_BLOCKED = "ERROR_CAPTCHAIMAGE_BLOCKED"
TOO_MANY_BAD_IMAGES = "TOO_MANY_BAD_IMAGES"

# Human readable descriptions of some errors for the user
errorLabels = {
	ERROR_WRONG_USER_KEY: _("API key is not specified"),
	ERROR_KEY_DOES_NOT_EXIST: _("Used a non-existent API key"),
	ERROR_ZERO_BALANCE: _("The balance of your account is zero"),
	ERROR_NO_SLOT_AVAILABLE: _("The current recognition rate is higher than the maximum set in the settings of Your account. Either on the server queue builds up and employees do not have time to disassemble it, repeat the sending captcha after 5 seconds"),
	ERROR_ZERO_CAPTCHA_FILESIZE: _("Size of the captcha is less than 100 bytes"),
	ERROR_TOO_BIG_CAPTCHA_FILESIZE: _("Size of the captcha more than 100 KB"),
	ERROR_IP_NOT_ALLOWED: _("In Your account you have configured restrictions based on IP from which you can make requests. And the IP from which the request is not included in the allowed list"),
	IP_BANNED: _("IP address from which the request is blocked because of frequent requests with various incorrect API keys. The lock is released in an hour"),
	ERROR_CAPTCHA_UNSOLVABLE: _("Captcha could not solve 3 different employee. Money for this image come back to balance"),
	ERROR_BAD_DUPLICATES: _("The error appears when 100 percent recognition. Has been used the maximum number of attempts, but the required number of identical answers has not been received"),
	ERROR_CAPTCHAIMAGE_BLOCKED: _("This captcha can not be recognized"),
	TOO_MANY_BAD_IMAGES: _("You are sending too many unrecognizable images. Please try again later"),
}

conf = {
	"graphicOnly": True,
	"regsense": False,
	"sizeReport": False,
	"textInstruction": False,
	"language": 0,
	"key": "",
}

class SettingsDialog(settingsDialogs.SettingsDialog):
	title = _("Captcha Solver Settings")

	def makeSettings(self, sizer):
		settingsSizerHelper = guiHelper.BoxSizerHelper(self, sizer=sizer)

		self.graphicOnly = wx.CheckBox(self, label=_("Recognize only &graphic objects"))
		self.graphicOnly.SetValue(conf["graphicOnly"])
		settingsSizerHelper.addItem(self.graphicOnly)

		self.regsense = wx.CheckBox(self, label=_("&Case sensitive recognition"))
		self.regsense.SetValue(conf["regsense"])
		settingsSizerHelper.addItem(self.regsense)

		self.sizeReport = wx.CheckBox(self, label=_("Report image &size"))
		self.sizeReport.SetValue(conf["sizeReport"])
		settingsSizerHelper.addItem(self.sizeReport)

		self.textInstruction = wx.CheckBox(self, label=_("Send &text instruction"))
		self.textInstruction.SetValue(conf["textInstruction"])
		settingsSizerHelper.addItem(self.textInstruction)

		self.language = settingsSizerHelper.addLabeledControl(_("Image &language:"), wx.Choice, choices=[_("Undefined"), _("Only Cyrillic alphabet"), _("Only Latin alphabet")])
		self.language.SetSelection(conf["language"])

		self.key = settingsSizerHelper.addLabeledControl(_("API &key:"), wx.TextCtrl, value=conf["key"])

	def postInit(self):
		self.graphicOnly.SetFocus()

	def onOk(self, event):
		conf["graphicOnly"] = self.graphicOnly.IsChecked()
		conf["regsense"] = self.regsense.IsChecked()
		conf["sizeReport"] = self.sizeReport.IsChecked()
		conf["textInstruction"] = self.textInstruction.IsChecked()
		conf["language"] = self.language.GetSelection()
		conf["key"] = self.key.GetValue()

		# Saves global conf into config file
		try:
			with open(FILE_CONFIG_PATH, "wb") as fileConfig:
				pickle.dump(conf, fileConfig, pickle.HIGHEST_PROTOCOL)
		except (IOError, OSError) as e:
			message.messageBox(e.strerror, _("Error saving settings"), style=wx.OK | wx.ICON_ERROR)

		super(SettingsDialog, self).onOk(event)

class RucaptchaError(RuntimeError):

	def __init__(self, error):
		super(RucaptchaError, self).__init__(error)
		self.error = error
		self.description = errorLabels.get(error)

class RucaptchaRequest(threading.Thread):

	def __init__(self, callback, **kwargs):
		super(RucaptchaRequest, self).__init__()
		self._callback = callback
		self._kwargs = kwargs
		self._host = "rucaptcha.com"
		self._connection = http.client.HTTPSConnection(self._host)
		self.daemon = True
		self.start()

	def run(self):
		resp = err = None
		try:
			resp = self._request(**self._kwargs)
		except OSError:
			err = _("Error connecting to server. Please check your Internet connection")
			log.exception()
		except RucaptchaError as ex:
			err = ex.description
			if err is None:
				err = _("Rucaptcha error: {error}").format(error=ex.error)
			log.exception()
		except Exception:
			err = _("Unexpected CaptchaSolver error. For details, see the NVDA log")
			log.exception()
		finally:
			self._connection.close()
		wx.CallAfter(self._callback, resp, err)

	def _request(self, **kwargs):
		kwargs["json"] = 1
		kwargs["key"] = conf["key"].encode("utf-8")

		if "body" not in kwargs:
			path = "/res.php?" + urlencode(kwargs)
			return self._HTTPRequest(path)

		kwargs["soft_id"] = 1665 # ID of CaptchaSolver from rucaptcha.com. Used for statistics
		kwargs["regsense"] = int(conf["regsense"])
		kwargs["language"] = conf["language"]
		kwargs["method"] = "base64"
		kwargs["body"] = base64.b64encode(kwargs["body"])

		captchaID = self._HTTPRequest("/in.php", body=urlencode(kwargs))

		queueHandler.queueFunction(queueHandler.eventQueue, speech.cancelSpeech)
		queueHandler.queueFunction(queueHandler.eventQueue, ui.message, _("Captcha successfully sent to the recognition. You will be notified when the result will be ready"))

		while True:
			time.sleep(2)
			try:
				return self._request(action="get", id=captchaID)
			except RucaptchaError as ex:
				if ex.error != CAPCHA_NOT_READY:
					raise ex

	def _HTTPRequest(self, path, body=None):
		method = "GET"
		headers = {"Host": self._host}
		if body:
			method = "POST"
			headers["Content-Type"] = "application/x-www-form-urlencoded"

		self._connection.request(method, path, body, headers)
		resp = self._connection.getresponse()
		if resp.status != http.client.OK:
			raise RuntimeError(f"{resp.status} {resp.reason}")

		respDict = json.load(resp)
		request = respDict.get("request")
		status = respDict.get("status")

		if status != 1:
			raise RucaptchaError(request)
		return request

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Captcha Solver")

	def __init__(self):
		super(GlobalPlugin, self).__init__()
		if globalVars.appArgs.secure:
			return

		# Updates global conf from config file
		try:
			with open(FILE_CONFIG_PATH, "rb") as fileConfig:
				conf.update(pickle.load(fileConfig))
		except Exception:
			pass

		# Creates submenu of addon
		captchaSolver_menu = wx.Menu()
		item = captchaSolver_menu.Append(wx.ID_ANY, _("Settings..."))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda evt: gui.mainFrame._popupSettingsDialog(SettingsDialog), item)
		item = captchaSolver_menu.Append(wx.ID_ANY, _("Account balance..."))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda evt: RucaptchaRequest(self.balanceDialog, action="getbalance"), item)
		item = captchaSolver_menu.Append(wx.ID_ANY, _("Profile on rucaptcha.com"))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda evt: webbrowser.open(RUCAPTCHA_PROFILE_URL), item)
		item = captchaSolver_menu.Append(wx.ID_ANY, _("Addon webpage"))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda evt: webbrowser.open(ADDON_URL), item)
		self.captchaSolver_menu = gui.mainFrame.sysTrayIcon.toolsMenu.AppendSubMenu(captchaSolver_menu, _("Captcha Solver"))

	def terminate(self):
		try:
			gui.mainFrame.sysTrayIcon.toolsMenu.Remove(self.captchaSolver_menu)
		except Exception:
			pass

	def balanceDialog(self, resp, err):
		if err is not None:
			message.messageBox(err, _("Error getting balance"), style=wx.OK | wx.ICON_ERROR)
			return

		message.messageBox(_("{:.2f}").format(float(resp)), _("Your account balance"))

	def captchaHandler(self, resp, err):
		if err is not None:
			ui.message(err)
			return

		api.copyToClip(resp)
		ui.message(_("Captcha solved successfully! The result copied to the clipboard"))

	def balanceHandler(self, resp, err):
		if err is not None:
			ui.message(err)
			return

		ui.message(_("Balance: {:.2f}").format(float(resp)))

	def _creator(self, **kwargs):
		if conf["textInstruction"]:
			dlg = wx.TextEntryDialog(gui.mainFrame, _("Instruction text (maximum {length} characters):").format(length=MAX_INSTRUCTION_LENGTH), _("Sending text instruction"))
			dlg.SetMaxLength(MAX_INSTRUCTION_LENGTH)
			gui.mainFrame.prePopup()
			status = dlg.ShowModal()
			gui.mainFrame.postPopup()
			textInstruction = dlg.GetValue()
			dlg.Destroy()
			if status != wx.ID_OK: return
			kwargs["textinstructions"] = textInstruction.encode("utf-8")
		RucaptchaRequest(self.captchaHandler, **kwargs)

	@script(description=_("Starts the recognition process"))
	def script_startRecognition(self, gesture):
		if globalVars.appArgs.secure:
			return

		from visionEnhancementProviders.screenCurtain import ScreenCurtainProvider
		screenCurtainId = ScreenCurtainProvider.getSettings().getId()
		screenCurtainProviderInfo = vision.handler.getProviderInfo(screenCurtainId)
		isScreenCurtainRunning = bool(vision.handler.getProviderInstance(screenCurtainProviderInfo))
		if isScreenCurtainRunning:
			ui.message(_("Please disable screen curtain before captcha recognizing"))
			return

		obj = api.getNavigatorObject()

		if obj.role != Role.GRAPHIC and conf["graphicOnly"]:
			ui.message(_("This object is not a graphical element"))
			return

		if State.OFFSCREEN in obj.states:
			ui.message(_("Captcha off screen"))
			return

		try:
			x, y, width, height = obj.location
		except Exception:
			ui.message(_("Captcha has no location"))
			return

		if conf["sizeReport"] and scriptHandler.getLastScriptRepeatCount() != 1:
			ui.message(_("Size: {width} X {height} pixels").format(width=width, height=height))
			return

		bmp = wx.Bitmap(width, height)
		mem = wx.MemoryDC(bmp)
		mem.Blit(0, 0, width, height, wx.ScreenDC(), x, y)
		image = bmp.ConvertToImage()
		body = io.BytesIO()
		image.SaveFile(body, wx.BITMAP_TYPE_PNG)

		wx.CallAfter(self._creator, body=body.getvalue())

	@script(description=_("Report account balance"))
	def script_getBalance(self, gesture):
		if globalVars.appArgs.secure:
			return
		RucaptchaRequest(self.balanceHandler, action="getbalance")

	@script(description=_("Show the settings dialog"))
	def script_showSettingsDialog(self, gesture):
		if globalVars.appArgs.secure:
			return
		gui.mainFrame._popupSettingsDialog(SettingsDialog)
