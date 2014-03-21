from lib import add_lib_path
add_lib_path()

import json
import logging

from jinja2 import Template
from google.appengine.api import urlfetch
from google.appengine.api import mail

import jsonpath
from muninn.agents import Agent
from pyquery import PyQuery as pq

import requests

urlfetch.set_default_fetch_deadline(30)


class ReadFormat(object):

    def get_value(self, key, obj):
        val = self.config.get(key)

        return self.render_value(val, obj)

    def render_value(self, val, obj):
        if obj is None or ("{{" not in val and "{%" not in val):
            return val
        return Template(val).render(event=obj)


    def _read_json(self, content, config):
        data = json.loads(content)
        responses = []
        if not "extract" in config:
            return data
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

    def _read_xml(self, content, config, parser="html", event=None):
        doc = pq(content, parser=parser)
        responses = []
        extract_config = config["extract"]

        tmp_responses = {}
        for key, config in extract_config.items():
            if 'selector' in config:
                els = doc(config['selector'])
                tmp_response = []
                for el in els:
                    if 'text' in config:
                        tmp_response.append(el.text)
                    elif 'html' in config:
                        tmp_response.append(el.html())
                    elif 'attr' in config:
                        tmp_response.append(el.attrib[config["attr"]])
                    else:
                        #we default on text
                        tmp_response.append(el.text)
                tmp_responses[key] = tmp_response
            elif 'static' in config:
                tmp_responses[key] = self.render_value(config['static'], event)

        keys = tmp_responses.keys()

        if len(keys) > 0:
            #we do not want to check static fields
            first_non_static = None
            for key in keys:
                if type(tmp_responses[key]) is list:
                    first_non_static = tmp_responses[key]
                    break

            for i in range(0, len(first_non_static)):
                response = dict()
                for key in keys:
                    if type(tmp_responses[key]) is list:
                        response[key] = tmp_responses[key][i]
                    else:
                        response[key] = tmp_responses[key]
                responses.append(response)
        return responses


class URLFetchAgent(Agent, ReadFormat):
    def do_request(self, event=None):
        config = self.config
        method = config.get("method", "GET").upper()
        response_kind = config.get("type", "JSON").upper()
        kwargs = {}

        if "params" in config:
            kwargs["params"] = {}
            for key in config['params'].keys():
                kwargs["params"][key] = self.get_value(key, config['params'])

        if "headers" in config:
            kwargs["headers"] = {}
            for key in config['headers'].keys():
                kwargs["headers"][key] = self.get_value(key, config['headers'])

        result = requests.request(method, self.get_value("url", event), **kwargs)

        if result.status_code != 200:
            logging.error('FETCH failed: %s' % result.status_code)
            return

        if response_kind == "JSON":
            new_events = self._read_json(result.content, config)
        elif response_kind == "XML":
            new_events = self._read_xml(result.content, config, parser="xml", event=event)
        else:
            new_events = self._read_xml(result.content, config, parser="html", event=event)

        for event in new_events:
            self.store.add_event(event)

    def run(self, events):
        if len(events) == 0:
            self.do_request()
        else:
            for event in events:
                self.do_request(event.data)
                event.done()


class EventGeneratorAgent(Agent):
    can_receive_events = False

    def run(self, events):
        config = self.config

        for event in config["events"]:
            self.store.add_event(event)


class PrintEventsAgent(Agent):
    can_generate_events = False

    def run(self, events):
        for event in events:
            logging.info(event.data)
            event.done()


class WebhookAgent(Agent, ReadFormat):

    def receive_webhook(self, request, response):
        config = self.config
        body = request.body

        kind = config.get("type", "JSON").upper()

        if kind == "JSON":
            response.content_type = 'application/json'
            new_events = self._read_json(body, config)
        elif kind == "XML":
            response.content_type = 'application/xml'
            new_events = self._read_xml(body, config, parser="xml")
        else:
            raise NotImplementedError()

        for event in new_events:
            self.store.add_event(event)

        if "response" in config:
            response.out.write(config["response"])
        elif kind == "JSON":
            response.out.write('{"result": "ok"}')
        elif kind == "XML":
            response.out.write("<result>ok</result>")


class EmailAgent(Agent):
    """
        Example of configuration:
        {
            "template_message": "Will need to put something clever here",
            "template_subject": "What the team did yesterday",
            "sender": "jane@example.com",
            "to": "john@example.com",
            "digest": 1
        }
    """

    can_generate_events = False

    def _send(self, data):
        config = self.config
        body = Template(config.get("template_message")).render(data=data)
        subject = Template(config.get("template_subject", "New events")).render(data=data)
        mail.send_mail(sender=config.get("sender"),
                       to=config.get("to"),
                       subject=subject,
                       body=body)

    def run(self, events):
        is_digest = self.config.get("digest", "0") == "1"

        if is_digest:
            data = [event.data for event in events]
            self._send(data)
            for event in events:
                event.done()
        else:
            for event in events:
                self._send(event.data)
                event.done()
