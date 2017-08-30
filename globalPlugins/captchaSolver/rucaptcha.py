import httplib
import io
import uuid
import wx
import urllib
import _config

HOST = 'rucaptcha.com'
BOUNDARY = uuid.uuid4().hex
SERVER = None

def requestAPI(**fields):
	try:
		image = fields.pop('image')
	except KeyError:
		image = None
	fields['key'] = _config.conf['key'].encode('utf-8')
	headers = {
		'Host': HOST,
		'Connection': 'close',
	}

	if image:
		body = io.BytesIO()
		for key in fields:
			body.write('--%s\r\n' % BOUNDARY)
			body.write('Content-Disposition: form-data; name="%s"\r\n\r\n' % key)
			body.write(str(fields[key]))
			body.write('\r\n')

		body.write('--%s\r\n' % BOUNDARY)
		body.write('Content-Disposition: form-data; name="file"; filename="image.png"\r\n\r\n')
		image.SaveStream(body, wx.BITMAP_TYPE_PNG)
		body.write('\r\n--%s--\r\n' % BOUNDARY)

		headers['Content-Type'] = 'multipart/form-data; boundary=%s' % BOUNDARY
		method = 'POST'
		path = '/in.php'
		body = body.getvalue()
	else:
		method = 'GET'
		path = '/res.php?' + urllib.urlencode(fields)
		body = None

	global SERVER
	Connection = httplib.HTTPSConnection if _config.conf['https'] else httplib.HTTPConnection
	if SERVER.__class__ != Connection:
		SERVER = Connection(HOST, timeout=10)
	try:
		SERVER.request(method, path, body, headers)
		response = SERVER.getresponse()
	except httplib.socket.gaierror, httplib.ssl.SSLError:
		return 'ERROR_CONNECTING_TO_SERVER'
	else:
		if response.status == 200:
			return response.read()
		else:
			return '{} {}'.format(response.status, response.reason)
	finally:
		SERVER.close()
