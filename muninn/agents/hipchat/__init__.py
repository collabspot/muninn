import logging
from jinja2 import Template
from muninn.agents import Agent
import hipchat


class HipchatAgent(Agent):
    can_generate_events = False

    @classmethod
    def run(cls, events, config, last_run):
        hipster = hipchat.HipChat(token=config.get("token"))

        for event in events:
            template = Template(config.get("template_message"))
            message = template.render(data = event.data)

            hipster.message_room(config.get("room_id"), config.get("sender", 'Munnin'), message)
