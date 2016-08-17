import httplib
import io
from uuid import uuid4
from urlparse import urlparse

URL = urlparse('https://rucaptcha.com/in.php')
BOUNDARY = uuid4().hex

def post(captcha, **fields):
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

	headers = {
		'Host': URL.hostname,
		'Content-Type': 'multipart/form-data; boundary=%s' % BOUNDARY,
	}

	server = httplib.HTTPSConnection(URL.hostname, timeout=10)
	try:
		server.request('POST', URL.path, body.getvalue(), headers)
		return server.getresponse().read()
	except httplib.socket.gaierror:
		return
	finally:
		server.close()
