import json
import jsonpath
import logging
from jinja2 import Template
from google.appengine.api import urlfetch
from google.appengine.api import mail
from muninn.agents import Agent


class URLFetchAgent(Agent):
    @classmethod
    def _read_json(cls, result, config):
        data = json.loads(result.content)
        responses = []
        #return data
        extract_config = config["extract"]
        logging.info(type(extract_config))

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

    @classmethod
    def _read_xml(cls, result, config):
        raise NotImplementedError()

    @classmethod
    def run(cls, events, config, store):
        method = urlfetch.GET if config.get("method", "GET").upper() == "GET" else urlfetch.POST
        response_kind = config.get("type", "JSON").upper()

        result = urlfetch.fetch(url=config["url"],
                                method=method)

        if result.status_code != 200:
            logging.error('FETCH failed: %s' % result.status_code)
            return

        if response_kind == "JSON":
            new_events = cls._read_json(result, config)
        else:
            new_events = cls._read_xml(result, config)

        for event in new_events:
            store.add_event(event)


class PrintEventsAgent(Agent):
    can_generate_events = False

    @classmethod
    def run(cls, events, config, store):
        for event in events:
            logging.info(event.data)


class EmailAgent(Agent):
    can_generate_events = False

    @classmethod
    def _send(cls, config, data):
        body = Template(config.get("template_message")).render(data=data)
        subject = Template(config.get("template_subject", "New events")).render(data=data)
        mail.send_mail(sender=config.get("sender", "jeremi@collabspot.com"),
                       to=config.get("to", "john@collabspot.com"),
                       subject=subject,
                       body=body)

    @classmethod
    def run(cls, events, config, store):
        is_digest = config.get("digest", "0") == "1"

        if is_digest:
            data = [event.data for event in events]
            cls._send(config, data)
        else:
            for event in events:
                cls._send(config, event.data)

