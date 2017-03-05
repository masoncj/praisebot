from praisebot.parse import PraiseMessage
from praisebot.template import Template


def render(message_text: str, **kwargs):
    """
    Given message string, parse it as a PraiseMessage, apply template, and return Render.
    :param message_text:
    :return:
    """
    message = PraiseMessage(message_text, **kwargs)

    # TODO: praise = message.make_praise()
    # and replace message with persistent praise below.
    context = message.get_context()
    template_name = message.template_name

    template = Template.locate(template_name)
    return template.apply(context)


class Bot(object):

    def connect(self):
        pass

    def loop(self):
        pass




