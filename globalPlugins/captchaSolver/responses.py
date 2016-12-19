import addonHandler

addonHandler.initTranslation()

responses = {
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
