import addonHandler
from versionInfo import version_year, version_major
import gui
import wx

addonHandler.initTranslation()
MIN_VERSION = (2019, 1)

def onInstall():
	if (version_year, version_major) < MIN_VERSION:
		gui.messageBox(_("CaptchaSolver incompatible with your NVDA version. CaptchaSolver requires NVDA {version} or later.").format(version=".".join(map(lambda n: str(n), MIN_VERSION))), _("Incompatible NVDA version"), style=wx.OK | wx.ICON_ERROR)
		raise RuntimeError("Incompatible NVDA version")
