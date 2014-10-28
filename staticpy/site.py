import os

from jinja2 import Environment, PackageLoader

from category import Category
from utils import copy_attrs, write_to_file


class Site(object):
    def __init__(self, settings, client_js_code='', include_drafts=False):
        '''A staticpy Site Object

        params:
            settings: an object defining
                - input_path: the full directory to the websites files
                - output_path: where you want the resulting files to go
                - base_url: the url where your website is hosted
            client_js_code: A piece of JS to communicate with the server
            include_drafts: Include pages that have not been published

        '''
        copy_attrs(self, settings, 'input_path', 'output_path', 'base_url')

        self.client_js_code = client_js_code
        self.include_drafts = include_drafts
        self.base = Category(
            self,
            os.path.join(self.input_path, 'dynamic', 'pages'),
        )

        self.env = Environment(loader=PackageLoader('dynamic', 'templates'))

    def save(self):
        self.base.write(self.output_path)
        self._render_sitemap()
        return self

    def _render_sitemap(self):
        template = self.env.get_template('sitemap.html')
        file_path = os.path.join(self.output_path, 'static', 'sitemap.xml')
        site_map = template.render(
            pages=self.sitemap_links,
            base_url=self.base_url
        )

        write_to_file(file_path, site_map)

    @property
    def sitemap_links(self):
        return [p for p in self.base.sub_pages if p.sitemap]

    @property
    def navigation_links(self):
        links = [p for p in self.base.sub_pages if p.include_in_navigation]
        return sorted(links, key=lambda x: x.order)
