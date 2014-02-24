import logging
from jinja2 import Template
from muninn.agents import Agent
import hipchat


class HipchatAgent(Agent):
    can_generate_events = False

    def run(self, events):
        config = self.config
        hipster = hipchat.HipChat(token=config.get("token"))
        template = Template(config.get("template_message"))

        for event in events:
            message = template.render(data=event.data)
            hipster.message_room(config.get("room_id"), config.get("sender", 'Munnin'), message)
