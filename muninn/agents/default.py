import json
import jsonpath
import logging
from jinja2 import Template
from google.appengine.api import urlfetch
from google.appengine.api import mail
from muninn.agents import Agent
from pyquery import PyQuery as pq


class URLFetchAgent(Agent):
    def _read_json(self, result, config):
        data = json.loads(result.content)
        responses = []
        extract_config = config["extract"]

        if type(extract_config) is unicode:
            return jsonpath.jsonpath(data, extract_config)
        else:
            tmp_responses = {}
            for key, expression in extract_config.items():
                tmp_responses[key] = jsonpath.jsonpath(data, extract_config[key])

            keys = tmp_responses.keys()

            if len(keys) > 0 and len(tmp_responses[keys[0]]):
                for i in range(0, len(tmp_responses[keys[0]])):
                    response = dict()
                    for key in keys:
                        response[key] = tmp_responses[key][i]
                    responses.append(response)
            return responses


    def _read_xml(cls, result, config, parser="html"):
        doc = pq(result.content, parser=parser)
        responses = []
        extract_config = config["extract"]

        tmp_responses = {}
        for key, config in extract_config.items():
            els = doc(config['selector'])
            tmp_response = []
            for el in els:
                if 'text' in config:
                    tmp_response.append(el.text())
                elif 'html' in config:
                    tmp_response.append(el.html())
                elif 'attr' in config:
                    tmp_response.append(el.attrib[config["attr"]])
                else:
                    #we default on text
                    tmp_response.append(el.text())
            tmp_responses[key] = tmp_response

        keys = tmp_responses.keys()

        if len(keys) > 0 and len(tmp_responses[keys[0]]):
            for i in range(0, len(tmp_responses[keys[0]])):
                response = dict()
                for key in keys:
                    response[key] = tmp_responses[key][i]
                responses.append(response)
        return responses


    def run(self, events):
        config = self.config
        method = urlfetch.GET if config.get("method", "GET").upper() == "GET" else urlfetch.POST
        response_kind = config.get("type", "JSON").upper()

        result = urlfetch.fetch(url=config["url"],
                                method=method)

        if result.status_code != 200:
            logging.error('FETCH failed: %s' % result.status_code)
            return

        if response_kind == "JSON":
            new_events = self._read_json(result, config)
        elif response_kind == "XML":
            new_events = self._read_xml(result, config, parser="xml")
        else:
            new_events = self._read_xml(result, config, parser="html")

        for event in new_events:
            self.agent.add_event(event)


class PrintEventsAgent(Agent):
    can_generate_events = False

    def run(self, events):
        for event in events:
            logging.info(event.data)


class EmailAgent(Agent):
    can_generate_events = False

    def _send(self, config, data):
        body = Template(config.get("template_message")).render(data=data)
        subject = Template(config.get("template_subject", "New events")).render(data=data)
        mail.send_mail(sender=config.get("sender", "jeremi@collabspot.com"),
                       to=config.get("to", "john@collabspot.com"),
                       subject=subject,
                       body=body)

    def run(self, events):
        config = self.config
        is_digest = config.get("digest", "0") == "1"

        if is_digest:
            data = [event.data for event in events]
            self._send(config, data)
        else:
            for event in events:
                self._send(config, event.data)
