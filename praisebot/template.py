import os
import textwrap
from typing import List

import cairosvg
import logging
import pybars
from pybars import PybarsError


logger = logging.getLogger(__name__)


# Search path dir arrays, relative to current file.
TEMPLATE_SEARCH_PATHS = [
    ["..", "templates"],
]


class TemplateSyntaxError(Exception):
    pass


class TemplateNotFoundError(Exception):
    pass


class Render(object):
    def __init__(self, svg_text):
        self.svg_text = svg_text

    def get_pdf_bytes(self):
        return cairosvg.svg2pdf(bytestring=self.svg_text.encode('utf-8'))

    def get_png_bytes(self):
        return cairosvg.svg2png(bytestring=self.svg_text.encode('utf-8'))


def wrap_helper(this, options, *args, **kwargs):
    width_chars = int(kwargs.get('width_chars', 30))
    height_pixels = float(kwargs.get('height_pixels', 30))
    wrapped_lines = textwrap.wrap("".join(args), width_chars)
    offset_y = 0.0
    result = []
    for line in wrapped_lines:
        context = {
            'x': '0',
            'y': offset_y,
            'text': line,
        }
        result.extend(options['fn'](context))
        offset_y += height_pixels
    return result


class Template(object):

    def __init__(self, name: str, path: str, template_text:str):
        self.name = name
        self.path = path

        compiler = pybars.Compiler()
        try:
            template = compiler.compile(template_text, path=self.path)
        except PybarsError as err:
            logger.exception("Failed to compile template: {}".format(path))
            raise TemplateSyntaxError(
                "Error compiling template {}: {}".format(self.name, str(err)))
        else:
            self.template = template

    @classmethod
    def locate(cls,
               template_name: str,
               search_paths: List[str]=TEMPLATE_SEARCH_PATHS,
               ) -> 'Template':
        """
        Given template name, search given filesystem paths for svg template.
        :param template_name:
        :param search_paths: (optional) list of filesystem paths to search.
        :return: a
        """
        assert os.sep not in template_name
        found_search_paths = []
        for search_path in search_paths:
            search_path = os.path.join(*search_path)
            if not os.path.isabs(search_path):
                search_path = os.path.join(os.path.dirname(__file__), search_path)
            if not os.path.exists(search_path):
                continue
            found_search_paths.append(search_path)
            template_path = os.path.join(search_path, "{}.svg".format(template_name))
            if os.path.exists(template_path):
                try:
                    with open(template_path) as template_file:
                        template_text = template_file.read()
                except OSError:
                    logger.exception("Error reading template from {}".format(template_path))
                else:
                    return cls(template_name, template_path, template_text)
        # If we reach this point, template has not been found.
        print(found_search_paths)
        templates = [
            filename
            for template_path in found_search_paths
            for filename in os.listdir(template_path)
            if filename.endswith('.svg')
        ]
        raise TemplateNotFoundError(
            "No such template {}.  Available templates: {}"
            .format(template_name, ", ".join(templates)))

    def apply(self, template_context) -> Render:
        template = self.template
        svg_text = template(template_context, helpers=self.get_helpers())
        return Render(svg_text)

    def get_helpers(self):
        return {
            'wrap': wrap_helper,
        }
