from datetime import datetime

from parsimonious import NodeVisitor
from parsimonious.grammar import Grammar

from praisebot.praise import Praise, User


class PraiseMessage(object):
    """
    Parses a chat message containing a demonstration of praise for a human being.

    Note this represents the parse of the expression in the chat message, not the chat message
    itself. This class has member variables that hold the result of the parsing expression.

    Syntax:

        @praisebot <template_name> @<user_to_thank> ("for") <text> with var=val(, var2=val2)+

        - <template_name> is the name of a handlebars template SVG file that is then printed on the
            sticker.
        - <user_to_thank> is mostly a template variable, but is also used to let the user know that
            they've been praised.
        - "for" is optional but makes the message sound more reasonable.  The template can decide
            whether or not to actually include the "for" in its output.
        - <message> is the actual text of the message of praise.  For convenience this is a bare,
            unquoted string.

    Examples:

        @praisebot thank @lucaswiman for writing gradgrind, a library that lets users write their
                      own spaghetti code
        @praisebot highfive @cmason
        @praisebot "thank and praise" @cmason for being awesome with icon="&#xf005;",
                      date="the future"
        @praise that @lucaswiman wrote gradgrind.

    Note that empty literals ("") below are to force Parsimonious to emit nodes in cases where
    otherwise a rule with a single RHS would not result in a node, preventing us from
    distinguishing the intermediate-level node.  (See discussion in 
    https://github.com/erikrose/parsimonious/issues/111 and thanks to @lucaswiman.)
    """
#         content               = (_ with_expr)? /  / ((_ FOR? _ text) _ with_expr)

    grammar = Grammar("""
        expression            = bot_user _ template_name _ recipient (_ message)?
        message               = FOR? _ text

        bot_user              = user_reference ""
        template_name         = string ""
        recipient             = (user_reference / channel_reference)  ""
        with_expr             = _ WITH _ variable_assignment
        variable_assignments  = (variable_assignment COMMA)* variable_assignment
        variable_assignment   = key EQUALS value
        key                   = string ""
        value                 = string ""
        text                  = reason_with_variable / reason

        FOR                   = "for"
        WITH                  = "with"
        _                     = ~"\s+"
        COMMA                 = "," _?
        EQUALS                = "="
        channel_reference     = ("<" channel ">" ) / channel
        user_reference        = ("<" user ">") / user
        user                  = "@" ~"[a-z0-9_-]+"i
        channel               = "#" ~"[a-z0-9_-]+"i
        string                = non_whitespace_string / double_quote_string / single_quote_string
        non_whitespace_string = ~'[^"s =]+'
        double_quote_string   = ~'"([^"=]|(\")|(\=))*"'
        single_quote_string   = ~"'([^'=]|(\')|(\=))*'"
        reason_with_variable  = ~"(.+?) with (.+)=(.+)"
        reason                = bare_string ""
        bare_string           = ~".+"
    """)

    class Visitor(NodeVisitor):
        def __init__(self, praise, get_user_fn):
            self.praise = praise
            self.get_user_fn = get_user_fn

        def get_user(self, user_reference):
            if user_reference.startswith("<"):
                user = self.get_user_fn(user_reference[2:-1])
            else:
                user = User(id=user_reference, name=user_reference,
                            full_name=user_reference, icon_url=None)
            return user

        def visit_bot_user(self, bot_user, _):
            user = self.get_user(bot_user.text)
            self.praise.bot_user = user.name
            self.praise.bot_user_name = user.full_name

        def visit_template_name(self, template_name, _):
            self.praise.template_name = template_name.text

        def visit_recipient(self, recipient, _):
            user = self.get_user(recipient.text)
            self.praise.recipient = user.name
            self.praise.recipient_name = user.full_name

        def visit_message(self, message, _):
            self.praise.message = message.text

        def visit_reason_with_variable(self, reason_with_variable, _):
            matching_groups = reason_with_variable.match.groups()
            self.praise.text = matching_groups[0]
            self.praise.variables = {matching_groups[1]: matching_groups[2]}

        def visit_reason(self, reason, _):
            self.praise.text = reason.text

        def visit_FOR(self, *args):
            self.praise.has_for = True

        def visit_variable_assignment(self, assignment, arg):
            (key, _, value) = assignment.children
            self.praise.variables[key.text] = value.text

        def generic_visit(self, node, visited_children):
            pass

    def __init__(self, message_text: str, praise:Praise=None, get_user_fn=None, **kwargs):
        self.praise = praise
        if not self.praise:
            self.praise = Praise()
        self.praise.update(kwargs)
        self.tree = self.grammar.parse(message_text)
        print(self.tree)
        self.Visitor(self.praise, get_user_fn).visit(self.tree)
