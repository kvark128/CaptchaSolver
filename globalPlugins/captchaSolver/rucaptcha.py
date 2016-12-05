import httplib
import io
import uuid
import urllib
import _config

HOST = 'rucaptcha.com'
BOUNDARY = uuid.uuid4().hex
HEADERS = {
	'Host': HOST,
}

def requestAPI(captcha=None, **fields):
	fields['key'] = _config.conf['key']

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

		HEADERS['Content-Type'] = 'multipart/form-data; boundary=%s' % BOUNDARY
		method = 'POST'
		path = '/in.php'
		body = body.getvalue()
	else:
		method = 'GET'
		path = '/res.php?' + urllib.urlencode(fields)
		body = None

	Connection = httplib.HTTPSConnection if _config.conf['https'] else httplib.HTTPConnection
	server = Connection(HOST, timeout=10)
	try:
		server.request(method, path, body, HEADERS)
		return server.getresponse().read()
	except httplib.socket.gaierror:
		return
	finally:
		server.close()
		try:
			del HEADERS['Content-Type']
		except KeyError:
			pass
