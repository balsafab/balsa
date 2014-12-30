import re, sys, time, webbrowser
import http.server, http.client, socketserver, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

class fab_handler(BaseHTTPRequestHandler):
    def __init__(self, bf, *args):
        self.bf = bf
        BaseHTTPRequestHandler.__init__(self, *args)
        
    def do_GET(self):
        x = self.bf.count()
        m = re.search(r"/balsafab\?code=([^/]*).*", str(self.path))
        if(not (m is None)):
            self.bf.done(m.group(1))
        else:
            self.bf.not_done()
        self.send_response(200)
        self.wfile.write(bytearray("Thanks","ASCII"))
        return
    def log_message(self, format, *args):
        return

class balsa_TCPServer(socketserver.TCPServer):
    allow_reuse_address = True

class balsafab:
    def __init__(self, app_id, client_secret):
        self.app_id = app_id
        self.secret = client_secret
        self.code = ""
        self.access_token = ""
        self.url = "https://www.facebook.com/dialog/oauth?client_id="+self.app_id+"&redirect_uri=http://localhost:3797/balsafab&scope=publish_actions"
        self.HOST = 'localhost'
        self.PORT = 3797
        self.found = False
        self.waiting = False
        self.counter = 0
        self.httpd = balsa_TCPServer((self.HOST, self.PORT), self.handler)

    def not_done(self):
        self.waiting = False
    def done(self, code):
        self.code = code
        self.found = True

    def count(self):
        self.counter += 1
        return self.counter

    def handler(self,*args):
        fab_handler(self, *args)

    def auth(self):
        webbrowser.open(self.url, new=1)
        self.waiting = True
        self.httpd.handle_request()
        while(not self.found):
            time.sleep(1)
            if(not self.waiting and not self.found):
                self.httpd.handle_request()
        token_url = "/oauth/access_token?client_id="+self.app_id+"&redirect_uri=http://localhost:3797/balsafab&client_secret="+self.secret+"&code="+self.code
        #print(token_url)
        conn = http.client.HTTPSConnection("graph.facebook.com")
        conn.request("GET", token_url)
        resp = conn.getresponse()
        data = resp.read()
        #print(str(data), resp.status)
        conn.close()
        m = re.search(r"access_token=([^&]*)", str(data))
        if(not m is None): 
            self.access_token = m.group(1)
        #print(self.access_token)

    def wallpost(self,text):
        params = urllib.parse.urlencode({"message":text,"access_token":self.access_token})
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        conn = http.client.HTTPSConnection("graph.facebook.com")
        conn.request("POST", "/me/feed", params, headers)
        resp = conn.getresponse()
        print(resp.status, resp.reason)
        data = resp.read()
        print(str(data))
        conn.close()
