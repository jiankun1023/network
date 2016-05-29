#!/usr/bin/python

import httplib
import socket
import string
import sys
import time
import urllib2
import ssl
from urllib2 import urlopen,HTTPError

ssl._create_default_https_context = ssl._create_unverified_context
TIMEOUT = 5  # seconds
NORMAL_FILES = [['/index.html', 'text/html'],
				['/foo/bar.html', 'text/html'],
				['/images/uchicago/logo.png', 'image/png']]
REDIRECTS = [['/nyt', 'http://www.nytimes.com/']]
NOTFOUNDS = ['/redirect.defs', '/not/a/real/url.html']

# prevents us from following redirects, so we can get the HTTP response code
class DontFollowHttpRedirectHandler(urllib2.HTTPRedirectHandler):
	def http_error_307(self, req, fp, code, msg, headers):
		raise urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp)
	http_error_302 = http_error_303 = http_error_307 

# reads file contents from disk, so we can compare with what the server returned.
def read_file(url):
    f = open('www' + url)
    return f.readlines()


class NonPersistentTestRunner:
	def __init__(self, host, port, scheme='http'):
		self._host = host
		self._port = port
		self._scheme = scheme
  
	def _build_url(self, filename):
		return '%s://%s:%s%s' % (self._scheme, self._host, self._port, filename)

	# returns request, response, code
	# response is null for 4xx or 5xx response
	def _maybe_fetch(self, filename, op='GET'):
		request = urllib2.Request(self._build_url(filename), headers={"Connection" : "close"})
		request.get_method = lambda : op
		opener = urllib2.build_opener(DontFollowHttpRedirectHandler)
		response = None
		try:
			response = opener.open(request)
		except HTTPError as e:
			return request, None, e.code
		return request, response, response.code

	def test_POST(self):
		for filename, mime_type in NORMAL_FILES:
			request, response, code = self._maybe_fetch(filename, op='POST')
			if code != 403:
				return False
		return True

	def test_INVALID(self):
		for filename, mime_type in NORMAL_FILES:
			request, response, code = self._maybe_fetch(filename, op='FOOBAR')
			if code != 403 and code < 500:
				return False
		return True

	def test_200(self, opcode='GET'):
		for filename, mime_type in NORMAL_FILES:
			print '\t%s' % (filename)
			request, response, code = self._maybe_fetch(filename, op=opcode)
			if code != 200 or response is None:
				return False
			if opcode=='HEAD' and len(response.readlines()) != 0:
				return False
			if opcode=='GET' and (response.readlines() != read_file(filename)):
				print 'Got different bytes back from server than read from local disk!'
				return False
			if mime_type != response.info().getheader('Content-Type'):
				print 'Unexpected MIME type ' + response.info().getheader('Context-Type') \
					+ ' for URL ' + filename
				return False
		return True

	def test_404(self, opcode='GET'):
		for filename in NOTFOUNDS:
			request, response, code = self._maybe_fetch(filename, op=opcode)
			if code != 404 or response != None:
				return False
		return True

	def test_301(self, opcode='GET'):
		for filename, redirect in REDIRECTS:
			request, response, code = self._maybe_fetch(filename, op=opcode)
			# because we followed the redirect, the code should actually be 200,
			# and there should be a response.
			if code != 200 or response == None:
				return False
			if response.url != redirect:
				return False
		return True

	def run_all_tests(self):
		results = {}

		test_list = {
			'200' : (self.test_200, 'GET'),
			'404' : (self.test_404, 'GET'),
			'301' : (self.test_301, 'GET'),
			'200 HEAD' : (self.test_200, 'HEAD'),
			'301 HEAD' : (self.test_301, 'HEAD'),
			'404 HEAD' : (self.test_404, 'HEAD'),
			'POST' : (self.test_POST, None),
			'INVALID' : (self.test_INVALID, None),
		}
	
		for test_case in test_list:
			func, op = test_list[test_case]
			try:
				if op:
					results[test_case] = func(opcode=op)
				else:
					results[test_case] = func()
			except Exception as e:
				results[test_case] = False
		return results


class PersistentTestRunner:
	def __init__(self, host, port):
		self._host = host
		self._port = port

	def test(self):
		response = ''
		conn = httplib.HTTPSConnection(self._host, self._port)
		for i in range(0, 2):
			conn.request('GET', '/index.html', headers={'Connection': 'Keep-Alive'})
			theresponse = conn.getresponse()
			if theresponse.status != 200:
				print 'Got a non-200 response, failing.'
				return False
			response = response + theresponse.read()
		conn.close()

		if not response:
			print 'response is None or empty, FAIL'
			return False
		return True

class SimultaneousTestRunner:
	def __init__(self, host, port, sslPort):
		self._host = host
		self._port = port
		self._sslPort = sslPort;

	def testSimultaneousConnections(self):
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error, msg:
			print 'error creating HTTP socket, FAIL', msg[1]
			return False
		
		try:
			sock.connect((self._host, int(self._port)))
		except socket.error, msg:
			print 'error connecting to HTTP socket, FAIL', msg[1]
			return False

		# leave the HTTP connection hanging, now that the server has returned from accept(),
		# and try the HTTPS connection
		response = urllib2.urlopen('https://%s:%s/index.html' % (self._host, int(self._sslPort)))
		return response.getcode() == 200
 
	
def parse_flags(argv):
	arg_map = {}
	if len(argv) <= 1: return {}
	for arg in argv[1:]:
		bits = arg.split('=')
		if len(bits) == 2:
			arg_map[bits[0]] = bits[1]
	return arg_map

# just iterate twice because this is a small list and it's simpler
def dump_results(result_map):
	print '\tPassing tests:'
	for label in result_map:
		if result_map[label]:
			print '\t\t' + label
	print '\tFailing tests:'
	for label in result_map:
		if not result_map[label]:
			print '\t\t' + label
	
		
if __name__  == '__main__':
	arg_map = parse_flags(sys.argv)
	if ('--host' not in arg_map) or ('--port' not in arg_map) or ('--sslport' not in arg_map):
		print 'usage: project2_autograder.py --host=linux2.cs.uchicago.edu --port=12345 --sslport=12346'
		sys.exit(-1)
	host = arg_map['--host']
	port = arg_map['--port']
	sslport = arg_map['--sslport']

	print '\n\nHTTP tests!'
	dump_results(NonPersistentTestRunner(host, port, 'http').run_all_tests())
	
	print '\n\nHTTPS tests!'
	dump_results(NonPersistentTestRunner(host, sslport, 'https').run_all_tests())

	print '\n\nPersistent tests!'
	if PersistentTestRunner(host, sslport).test():
		print 'PASSED'
	else:
		print 'FAILED'

	print '\n\nSimultaneous tests!'
	try:	
		simultaneous = SimultaneousTestRunner(host, port, sslport).testSimultaneousConnections()
	except Exception as e:
		print e
		simultaneous = False		
	if simultaneous:
		print 'PASSED'
	else:
		print 'FAILED'
