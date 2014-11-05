from __future__ import absolute_import

import os

from jinja2 import Environment, PackageLoader

from ..utils import write_to_file


class Sitemap(object):
    def __init__(self, site):
        self.env = Environment(loader=PackageLoader('dynamic', 'templates'))
        self.site = site

    def write(self):
        template = self.env.get_template('sitemap.html')
        file_path = os.path.join(
            self.site.output_path,
            'static',
            'sitemap.xml'
        )
        site_map = template.render(
            pages=self.pages,
            base_url=self.site.base_url
        )

        write_to_file(file_path, site_map)

    @property
    def pages(self):
        return [p for p in self.site.pages if p.sitemap]
