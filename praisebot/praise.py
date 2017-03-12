from collections import namedtuple
from datetime import datetime


class User(namedtuple('_User', ('id', 'name', 'full_name', 'icon_url'))):
    """
    A Slack User or Bot.
    """
    pass


class Praise(object):
    # TODO: make this persistent

    FIELDS = [
        'message', 'text',
        'recipient', 'recipient_name',
        'bot_user',
        'sender', 'sender_name',
    ]

    def __init__(self, **kwargs):
        self.message = ""  # Full message include "for"
        self.text = ""  # Bare message text
        self.variables = kwargs
        self.has_for = False
        self.has_with = False
        self.template_name = None

    def update(self, d):
        for field in self.FIELDS:
            value = d.get(field, None)
            setattr(self, field, value)

    def get_context(self) -> dict:
        context = {}
        for field in self.FIELDS:
            context[field] = getattr(self, field, None)
        context['date'] = datetime.now().strftime("%-I:%M%p %d %b %Y")
        context['date_numeric'] = datetime.now().strftime("%Y%m%d%H%M")
        context.update(self.variables)
        return context
