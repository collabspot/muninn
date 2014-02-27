import logging
import webapp2
from muninn.models import AgentStore


class WebhookHandler(webapp2.RequestHandler):
    def get(self, agent_id, secret):
        self.response.set_status(405)

    def post(self, agent_id, secret):

        store = AgentStore.get_by_id(int(agent_id))
        try:
            if 'secret' in store.config and store.config['secret'] != secret:
                self.response.set_status(403)
                return

            store.receive_webhook(self.request, self.response)
        except Exception, e:
            logging.exception(e)
            raise e
        else:
            logging.debug('Done.\n')

app = webapp2.WSGIApplication([
    ('/webhook/([0-9]*)/(.*)/?', WebhookHandler),
], debug=True)
