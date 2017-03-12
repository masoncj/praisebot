import logging
import sys
from argparse import ArgumentParser
from configparser import ConfigParser
from logging.config import fileConfig
from os import path
from time import sleep

from lru import LRUCacheDict
from parsimonious import Grammar
from parsimonious import NodeVisitor

from praisebot.parse import PraiseMessage
from praisebot.praise import User
from praisebot.template import Template, Render
from slackclient import SlackClient


logger = logging.getLogger('bot')


def render_message(message_text: str, get_user_fn=None, **kwargs) -> Render:
    """
    Given message string, parse it as a PraiseMessage, apply template, and return Render.

    :param message_text: The text of the message that mentions praisebot.
    :param kwargs: additional template context variables.  You'll likely want to include at least
     `sender` and `sender_name`.  See templates README for more details.
    :return: a Render of the given praise
    """
    message = PraiseMessage(message_text, get_user_fn=get_user_fn, **kwargs)
    praise = message.praise
    context = praise.get_context()
    template_name = praise.template_name

    template = Template.locate(template_name)
    output = template.apply(context)
    output.message = message
    output.praise = praise
    return output


class SlackUploadError(Exception):
    pass


class SlackUserNotFoundError(Exception):
    pass


class SlackMessage(NodeVisitor):
    """
    Slack message have embedded user, channel, and URL references.  Here we process these into
    regular @user or #channel mentions.
    """

    grammar = Grammar("""
           expression = (mention / text)*
           mention = "<" ~"[^>]+" ">"
           text = ~"[^<]+"
       """)

    def __init__(self, message_text, bot):
        self.bot = bot
        self.text = ""
        while message_text:
            tree = self.grammar.match(message_text)
            self.visit(tree)
            message_text = message_text[tree.end+1:]

    def visit_mention(self, mention, _):
        mention_name = mention.text[1:-1]  # Strip <>.
        mention_name = mention_name.split("|")[0]  # Strip |.*
        if mention_name.startswith("@"):
            user = self.bot.get_user(mention_name[1:])
            self.text += '@' + user.name
        elif mention_name.startswith('#'):
            # Channels not handled yet.
            pass
        else:
            self.text += mention_name

    def visit_text(self, text, _):
        self.text += text.text

    def generic_visit(self, node, visited_children):
        pass


class Bot(object):
    """
    The Praise bot.

    Listens for message of praise on Slack using the [RTM API](https://api.slack.com/rtm). Renders
    praises back to the channel and (optionally) prints to label printer.
    """

    def __init__(self, config):
        self.config = config
        self.sc = SlackClient(config['slack_api_token'])
        self.username = None
        self.user = None
        self.users = LRUCacheDict(max_size=500, expiration=60)

    def get_user(self, user_id: str) -> User:
        """
        Given alphanumeric user identifier (eg `U023BECGF`), returns a User object.
        """
        try:
            user = self.users[user_id]
        except KeyError:  # Lame.
            user = None
        if not user:
            result = self.sc.api_call('users.info', user=user_id)
            if result['ok']:
                result = result['user']
                profile = result['profile']
                user = User(id=user_id, name='@' + result['name'], full_name=profile['real_name'],
                            icon_url=profile['image_512'])
            elif result['error'] == 'user_not_found':
                # Grr bots are people too, Slack...
                result = self.sc.api_call('bots.info', bot=user_id)
                if result['ok']:
                    bot = result['bot']
                    user = User(id=user_id, name=bot['name'], full_name=bot['name'],
                                icon_url=bot['icons']['image_72'])
                else:
                    logger.error('Error in bots.info %s: %s', user_id, result)
            else:
                logger.error("Error in users.profile.get %s: %s", user_id, result)

        if not user:
            raise SlackUserNotFoundError("Cannot find user {}".format(user_id))
        self.users[user_id] = user
        return user

    def upload_image(self, render: Render, channel=None) -> dict:
        """
        Given Render, upload PNG image to Slack and return resulting Slack file object.

        :param render: a Render.
        :return: JSON dict of resulting Slack file object.
        :raises: SlackUploadError if upload fails for any reason.
        """
        meta = render.metadata

        result = self.sc.api_call(
            'files.upload',
            file=render.png_bytes,
            filename=meta['filename'],
            title=meta['title'],
            channels=channel,
        )
        if not result.get('ok', None):
            raise SlackUploadError(
                "Unable to upload render {filename} of template {template} to Slack: {error}"
                .format(
                    filename=meta.get('filename', None),
                    template=render.template.name,
                    error=result.get('error', "<unknown error>")
                )
            )
        file = result['file']
        logger.info("Uploaded %s: %s",
                    meta['filename'],
                    file,
                    )
        # result = self.sc.api_call(
        #     'files.sharedPublicURL',
        #     file=file['id']
        # )
        # if not result.get('ok', None):
        #     raise SlackUploadError(
        #         "Unable to share file {id} {filename}: {error}"
        #             .format(
        #             id=file['id'],
        #             filename=meta.get('filename', None),
        #             error=result.get('error', "<unknown error>")
        #         )
        #     )
        return result['file']

    def preprocess_message(self, message_text):
        message = SlackMessage(message_text, self)
        return message.text

    def process_praise_message(self, message_text, **kwargs):
        user = self.get_user(kwargs['user'])
        render = render_message(
            message_text,
            sender=user.name,
            sender_name=user.full_name,
            get_user_fn=lambda user_id: self.get_user(user_id),
            **kwargs)
        meta = render.metadata
        file = self.upload_image(render, channel=kwargs['channel'])
        message = {
            'channel': kwargs['channel'],
            'as_user': False,
            'username': self.username,
            'text': meta['message'],
            "attachments": [
                {
                    "fallback": meta['title'],
                    "title": meta['title'],
                    "image_url": file['url_private_download'],
                }
            ],
        }
        self.sc.api_call('chat.postMessage', **message)
        logger.info("Posted %s for %s in %s: %s",
                    render.template.name,
                    render.praise.recipient,
                    kwargs['channel'],
                    render.metadata['title'])

    def process_message(self, message_text, **kwargs):
        if 'messages' in self.config.get('DEBUG', ''):
            logger.debug(message_text)

        if message_text.startswith('<@' + self.user.id + '>'):
            self.process_praise_message(message_text, **kwargs)

    def process(self, msg):
        if 'raw_messages' in self.config.get('DEBUG', ''):
            logger.debug(msg)
        if msg['type'] == 'message':
            self.process_message(msg['text'], **msg)
        elif msg['type'] == 'error':
            raise ValueError(msg['error']['msg'])

    def run(self):
        keep_going = True
        while keep_going:
            try:
                # Note: self.sc.rtm_connect() unhelpfully returns true or false instead of raising.
                self.sc.server.rtm_connect()
                # I'm not sure why slack chose to make the default nonblocking but it uses
                # 100% CPU unless we introduce an arbitrary wait.
                self.sc.server.websocket.sock.setblocking(1)
            except KeyboardInterrupt:
                logger.info("Exiting...")
                keep_going = False
            except Exception:
                logger.exception("Error connecting to Slack, retrying...")
                sleep(1)
            else:
                self.username = self.sc.server.username
                self.user_id = self.sc.server.users.find(self.username).id
                self.user = self.get_user(self.user_id)
                logger.info("Connected to Slack as {}.".format(self.username))
                msg = None
                while keep_going:
                    try:
                        messages = self.sc.rtm_read()
                        for msg in messages:
                            self.process(msg)
                    except KeyboardInterrupt:
                        print("Exiting...")
                        keep_going = False
                    except Exception:
                        logger.exception("Error processing message '{}'".format(msg))


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    parser = ArgumentParser(description='Run praisebot Slack bot.')
    parser.add_argument(
        "-c", "--config",
        dest='config',
        help='Path to ini file containing slack API key and other configuration.',
        default='config.ini'
    )
    args = parser.parse_args()
    config_file_path = args.config
    config = ConfigParser()
    config.read(config_file_path)

    #fileConfig(config)

    logger.info("Praisebot starting with configuration from {}."
                .format(path.abspath(config_file_path)))

    bot = Bot(config['DEFAULT'])
    bot.run()



