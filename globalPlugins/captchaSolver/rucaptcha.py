import httplib
import io
import uuid
import urllib
import _config

HOST = 'rucaptcha.com'
BOUNDARY = uuid.uuid4().hex
SERVER = None

def requestAPI(captcha=None, **fields):
	fields['key'] = _config.conf['key']
	headers = {
		'Host': HOST,
		'Connection': 'close',
	}

	if captcha:
		body = io.BytesIO()
		for key in fields:
			body.write('--%s\r\n' % BOUNDARY)
			body.write('Content-Disposition: form-data; name="%s"\r\n\r\n' % key)
			body.write(str(fields[key]))
			body.write('\r\n')

		body.write('--%s\r\n' % BOUNDARY)
		body.write('Content-Disposition: form-data; name="file"; filename="captcha.png"\r\n\r\n')
		body.write(captcha)
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
		return
	else:
		if response.status == 200:
			return response.read()
		else:
			return '{} {}'.format(response.status, response.reason)
	finally:
		SERVER.close()
