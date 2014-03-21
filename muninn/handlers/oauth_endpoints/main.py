import logging
from urlparse import parse_qs
import webapp2
from config import TWITTER_CLIENT_KEY, TWITTER_SECRET_KEY
import config
from muninn.models import Credential
from muninn.utils import force_str
import requests
from requests.packages import urllib3
from requests_oauthlib import OAuth2Session, OAuth1, OAuth1Session


class TwitterHandler(webapp2.RequestHandler):
    request_token_url = "https://api.twitter.com/oauth/request_token"
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    access_token_url = "https://api.twitter.com/oauth/access_token"
    client_key = config.TWITTER_CLIENT_KEY
    client_secret = config.TWITTER_SECRET_KEY

    def get(self, command):
        logging.info(command)
        if command == "login":
            #step1
            oauth = OAuth1Session(self.client_key, client_secret=self.client_secret)
            fetch_response = oauth.fetch_request_token(self.request_token_url)
            resource_owner_key = fetch_response.get('oauth_token')
            resource_owner_secret = fetch_response.get('oauth_token_secret')
            self.response.set_cookie('twitter_resource_owner_key', resource_owner_key, max_age=360, path='/', secure=True)
            self.response.set_cookie('twitter_resource_owner_secret', resource_owner_secret, max_age=360, path='/', secure=True)

            authorization_url = oauth.authorization_url(self.base_authorization_url)
            self.redirect(force_str(authorization_url))

        elif command == "callback":
            #step2
            oauth = OAuth1Session(self.client_key,
                                  client_secret=self.client_secret,
                                  resource_owner_key=self.request.cookies.get('twitter_resource_owner_key'),
                                  resource_owner_secret=self.request.cookies.get('twitter_resource_owner_secret'))

            oauth_response = oauth.parse_authorization_response(self.request.url)
            verifier = oauth_response.get('oauth_verifier')

            #step3
            oauth = OAuth1Session(self.client_key,
                          client_secret=self.client_secret,
                          resource_owner_key=self.request.cookies.get('twitter_resource_owner_key'),
                          resource_owner_secret=self.request.cookies.get('twitter_resource_owner_secret'),
                          verifier=verifier)
            oauth_tokens = oauth.fetch_access_token(self.access_token_url)

            #this are the tokens to save
            resource_owner_key = oauth_tokens.get('oauth_token')
            resource_owner_secret = oauth_tokens.get('oauth_token_secret')

            Credential(name="Twitter", credential_type="oauth2", data={
                "resource_owner_key": resource_owner_key,
                "resource_owner_secret": resource_owner_secret
            }).put()

            self.redirect("/")
            return

    def post(self):
        pass


class GithubHandler(webapp2.RequestHandler):
    # This information is obtained upon registration of a new GitHub
    client_id = config.GITHUB_CLIENT_KEY
    client_secret = config.GITHUB_SECRET_KEY
    authorization_base_url = 'https://github.com/login/oauth/authorize'
    token_url = 'https://github.com/login/oauth/access_token'

    def get(self, command):
        logging.info(command)
        if command == "login":
            github = OAuth2Session(self.client_id)
            authorization_url, state = github.authorization_url(self.authorization_base_url)

            # State is used to prevent CSRF, keep this for later.
            self.response.set_cookie('oauth_state', state, max_age=360, path='/', secure=True)
            self.redirect(force_str(authorization_url))
            return
        elif command == "callback":

            github = OAuth2Session(self.client_id, state=self.request.cookies.get('oauth_state'))
            token = github.fetch_token(self.token_url, client_secret=self.client_secret,
                                       authorization_response=self.request.url)

            Credential(name="Github", credential_type="oauth2", data=token).put()

            self.redirect("/")
            return

    def post(self):
        pass

class GoogleHandler(webapp2.RequestHandler):
    # This information is obtained upon registration of a new GitHub
    client_id = config.GOOGLE_CLIENT_KEY
    client_secret = config.GOOGLE_SECRET_KEY
    authorization_base_url = 'https://accounts.google.com/o/oauth2/auth'
    token_url = 'https://accounts.google.com/o/oauth2/token'
    redirect_uri = 'https://jeremi-munnin.appspot.com/oauth/google/callback/'
    scope = ['https://www.googleapis.com/auth/userinfo.email',
             'https://www.googleapis.com/auth/userinfo.profile']

    def get(self, command):
        if command == "login":
            google = OAuth2Session(self.client_id, scope=self.scope, redirect_uri=self.redirect_uri)

            authorization_url, state = google.authorization_url(self.authorization_base_url,
                # offline for refresh token
                # force to always make user click authorize
                access_type="offline", approval_prompt="force")

            # State is used to prevent CSRF, keep this for later.
            self.response.set_cookie('google_oauth_state', state, max_age=360, path='/', secure=True)
            self.redirect(force_str(authorization_url))
            return
        elif command == "callback":
            google = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri,
                          scope=self.scope, state=self.request.cookies.get('oauth_state'))

            token = google.fetch_token(self.token_url, client_secret=self.client_secret,
                authorization_response=self.request.url)

            Credential(name="Google", credential_type="oauth2", data=token).put()
    
            self.redirect("/")
            return

    def post(self):
        pass



app = webapp2.WSGIApplication([
    ('/oauth/github/(.*)/', GithubHandler),
    ('/oauth/google/(.*)/', GoogleHandler),
    ('/oauth/twitter/(.*)/', TwitterHandler),
], debug=True)
