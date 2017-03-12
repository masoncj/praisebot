from unittest import TestCase

import re

import magic

from praisebot.bot import render_message
from praisebot.template import TemplateNotFoundError, Template, TemplateSyntaxError


class TestTemplate(TestCase):

    def test_nonexistent_template(self):
        with self.assertRaisesRegex(TemplateNotFoundError, "Available.*thank.*"):
            Template.locate("asdfghj")

    def test_error_template(self):
        with self.assertRaisesRegex(TemplateSyntaxError, ".*Error at character 5.*"):
            Template("test", "test", "{{#if")

    def test_no_path_separators(self):
        with self.assertRaises(AssertionError):
            Template.locate('/etc/password')

    def test_render(self):
        render = render_message(
            "@praisebot thank @cmason for being an all-around awesome dude and "
            "helping sing the praises of others!",
            sender='@priscilla',
            message_id='hteq3a',
        )
        self.assertIn("cmason", render.svg_text)
        self.assertIn("thank", render.svg_text)

        png_bytes = render.png_bytes
        pdf_bytes = render.pdf_bytes

        magic_db = magic.Magic(mime=True, uncompress=True)

        self.assertEqual(magic_db.from_buffer(png_bytes), 'image/png')
        self.assertEqual(magic_db.from_buffer(pdf_bytes), 'application/pdf')

        with open("/tmp/out.png", 'wb') as out_file:
            out_file.write(png_bytes)

        with open("/tmp/out.pdf", 'wb') as out_file:
            out_file.write(pdf_bytes)

        meta = render.metadata
        self.assertEqual(meta['title'], "@priscilla thanked @cmason")

        text = render.raw_text
        self.assertIn('@priscilla thanked @cmason', text)

    def test_wrap(self):
        template_text = """
            {{#wrap message width_chars="30" height_pixels="22" }}
                <tspan x="{{x}}" y="{{y}}" class="st0 st6 st9">{{text}}</tspan>
            {{/wrap}}
        """
        message_text = """
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam nulla nisl, sagittis a
            ultricies nec, vulputate sed mauris. Praesent pharetra, felis vitae consectetur aliquet,
            orci orci pulvinar ligula, vitae condimentum purus nunc sed arcu. Curabitur a dignissim
            leo. Morbi et eleifend urna. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            Integer sed magna a lorem commodo rhoncus. Nullam feugiat scelerisque consectetur.
            """
        message_text = re.sub("\n\s+", ' ', message_text)
        self.assertNotIn( '\n', message_text)

        template = Template("test", "test", template_text)

        svg_str = template.apply({'message': message_text}).svg_text
        self.assertEqual(
            svg_str.count('/tspan'),
            16)
