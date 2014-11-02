from __future__ import absolute_import

import os

from jinja2 import Environment, PackageLoader

from ..utils import write_to_file


class Writer(object):

    def __init__(self, page):
        self.category = page.category
        self.site = page.site
        self.page = page

    def write(self):
        write_to_file(self.path, self._render())

    @property
    def path(self):
        return '{path}.html'.format(
            path=os.path.join(
                self.site.output_path,
                self.category.url_path,
                self.page.slug
            ),
        )

    @property
    def template(self):
        env = Environment(
            loader=PackageLoader('dynamic', 'templates')
        )
        return env.get_template(
            self.page.template_name
        )

    def _render(self):
        return self.template.render(
            page=self.page,
            category=self.category,
            navigation_links=self.site.navigation_links,
            client_js_code=self.site.client_js_code,
        )
