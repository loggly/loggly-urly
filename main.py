#!/usr/bin/env python
#
# Copyright 2008 Adam Stiles
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy 
# of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required 
# by applicable law or agreed to in writing, software distributed under the 
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS 
# OF ANY KIND, either express or implied. See the License for the specific 
# language governing permissions and limitations under the License.
#

"""A url-shortener built on Google App Engine."""
__author__ = 'Adam Stiles'

""" 
All Urly records in the database have an id and an href. We base62 that
integer id to create a short code that represents that Urly.

Format options are: json, xml, html, and txt

/{code}                     Redirect user to urly with this code
/{code}(.format)            Show user formatted urly with this code
/new(.format)?href={href}   Create a new urly with this href or
                            return existing one if it already exists
                            Note special handling for 'new' code
                            when we have a href GET parameter 'cause
                            'new' by itself looks like a code
"""
import wsgiref.handlers
import re, os, logging
from google.appengine.ext import webapp
from google.appengine.ext import db
from urly import Urly
from view import MainView
import loggly

HOOVER = loggly.LogglyLogger('http://logs.loggly.com/inputs/7e7a83a8-3f2b-457e-9a1a-7805c0329d6f', logging.INFO)

# do some redirect shizzle for the bizzle that is izzle
class RedirectHandler(webapp.RequestHandler):
    def get(self, group):
        self.redirect('http://www.loggly.com/%s' % group)

class MainHandler(webapp.RequestHandler):
    """All non-static requests go through this handler.
    The code and format parameters are pre-populated by
    our routing regex... see main() below.
    """
    def get(self, code, format):
        if (code is None):
            logging.info("someone thinking about crafting a URL")
            MainView.render(self, 200, None, format)
            return

        ip = self.request.remote_addr 
        href = self.request.get('href').strip().encode('utf-8')
        title = self.request.get('title').strip().encode('utf-8')
        if (code == 'new') and (href is not None):
            try:
                u = Urly.find_or_create_by_href(href)
                if u is not None:
                    logging.info("creating urly by href: %s", str(href))
                    MainView.render(self, 200, u, format, href, title)
                else:
                    logging.info("error creating urly by href: %s", str(href))
                    MainView.render(self, 400, None, format, href)
            except db.BadValueError:
                # href parameter is bad
                logging.info("error with parameter")
                MainView.render(self, 400, None, format, href)
        else:
            u = Urly.find_by_code(str(code))
            if u is not None:
                logging.info("http://logg.ly/%s redirecting to %s for %s" % (code, u.href, ip))
                MainView.render(self, 200, u, format)
            else:
                logging.info("redirecting to loggly.com/%s" % code)
                self.redirect('http://www.loggly.com/%s' % code)
    
    def head(self, code, format):
        if (code is None):
            self.error(400)
        else:
            u = Urly.find_by_code(str(code))
            if u is not None:
                self.redirect(u.href)
            else:
                self.error(404)

def main():
    # max key length is 3, otherwise we redirect to loggly
    application = webapp.WSGIApplication([
       ('/([a-zA-Z0-9]{1,3})?(.xml|.json|.html|.txt)?', MainHandler), 
       ('/(.*?)', RedirectHandler) 
    ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
