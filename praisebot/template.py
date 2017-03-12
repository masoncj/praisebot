import os
import textwrap
import uuid
from typing import List
from xml.etree import ElementTree

import cairosvg
import logging
import pybars
import re
from cached_property import cached_property
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
    """
    A renderer for the visual representation of a praise.

    The result of executing a Template against a context derived from a chat message, this class
    wraps the resulting SVG text and enables rendering it to various output formats such as
    PDF or PNG.
    """
    def __init__(self, svg_text, template):
        self.svg_text = svg_text
        self.template = template
        self.namespaces = {
            'svg': 'http://www.w3.org/2000/svg',
        }

    @property
    def pdf_bytes(self):
        return cairosvg.svg2pdf(bytestring=self.svg_text.encode('utf-8'))

    @property
    def png_bytes(self):
        return cairosvg.svg2png(bytestring=self.svg_text.encode('utf-8'))

    @cached_property
    def element_tree(self):
        return ElementTree.fromstring(self.svg_text)

    @cached_property
    def raw_text(self):
        """
        Return the plain text content of the rendered template, with all XML formatting removed.

        Note that, depending on the ordering of the text in the SVG image, the resulting text
        from this method may not be very intelligible.
        """
        text = ElementTree.tostring(self.element_tree, encoding='utf-8', method='text')
        text = text.decode('utf-8')
        text = re.sub(u'\s+', u' ', text)
        return text

    def _strip_ns(self, name):
        for ns_url in self.namespaces.values():
            name = name.replace("{" + ns_url + "}", "")
        return name

    @cached_property
    def metadata(self) -> dict:
        """
        Return dict containing metadata elements from SVG text include title and filename.

        The following metadata elements are guaranteed to exist, although a warning will be
        generated (and resulting value will be less ideal) if not present in SVG template:

        * `title`: A short, human-meaningful description.  (Note: title is taken from the top-level
           standard "title" tag of the SVG, and not nested in the metadata tag.)
        * `filename`: a unique filename for the rendered image, not include file extension.
        * `message`: a plain text version of the rendered image.
        """
        et = self.element_tree
        metadata_elements = et.findall('.//svg:metadata', self.namespaces)
        metadata = {
            self._strip_ns(meta.tag): meta.text for metas in metadata_elements for meta in metas
        }
        title = et.find('.//svg:title', self.namespaces)
        if title is not None:
            metadata['title'] = title.text
        else:
            logger.warning("Template {} has no title element.".format(self.template.name))
            metadata['title'] = self.raw_text

        filename = metadata.get('filename', None)
        if not filename:
            logger.warning("Template {} has no filename metadata.".format(self.template.name))
            metadata['filename'] = uuid.uuid4().hex

        message = metadata.get('message', None)
        if not message:
            logger.warning("Template {} has no message element.".format(self.template.name))
            metadata['message'] = self.raw_text

        return metadata


def wrap_helper(this, options, *args, **kwargs):
    """
    Handlebars helper for simple text line wrapping.

    Positional arguments give the concatenated text to wrap.  In addition, takes two named
    arguments:
    :param width_chars: The width, in characters, at which to wrap.  Text will wrap at word
    boundaries resulting in lintes of less than this length.
    :param height_pixels: The line height, in pixels, to add to each successive line of wrapped
    text in the y dimension.
    """
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
    """
    Template SVG file for visual representation of a praise.

    Responsible for locating and executing a handlebars template given a context dictionary
    derived from a chat message.
    """

    def __init__(self, name: str, path: str, template_text:str):
        self.name = name
        self.path = path

        compiler = pybars.Compiler()
        try:
            template = compiler.compile(template_text)
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

        :param template_name: string name of template to search for.  Must not contain path
        separators.
        :param search_paths: (optional) list of filesystem paths to search.
        :return: a Template.
        :raises: TemplateNotFoundError if a template of the given name cannot be located.
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

    def apply(self, template_context: dict) -> Render:
        """
        Given a template context dictionary apply the template to that context and return resulting
        SVG text as a Render.

        :param template_context: a dict containing the variables to use in applying the template.
        :return: a Render wrapping the resulting SVG text.
        """
        template = self.template
        svg_text = template(template_context, helpers=self.get_helpers())
        return Render(svg_text, self)

    def get_helpers(self):
        return {
            'wrap': wrap_helper,
        }
