import addonHandler
from versionInfo import version_year, version_major
import gui
import wx

addonHandler.initTranslation()

def onInstall():
	if (version_year, version_major) < (2017, 3):
		gui.messageBox(_('CaptchaSolver incompatible with your version of NVDA. CaptchaSolver requires NVDA 2017.3 or above.'), _('Incompatible version of NVDA'), style=wx.OK | wx.ICON_ERROR)
		raise RuntimeError('Incompatible version of NVDA')
