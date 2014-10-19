import os

from jinja2 import Environment, PackageLoader

from category import Category
from utils import copy_attrs


def _write_to_file(fp, contents):
    with open(fp, 'w') as output:
        output.write(contents)


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
        self._write_category(self.base)
        self._render_sitemap()
        return self

    def _init_category(self, category_path):
        if not os.path.isdir(category_path):
            os.mkdir(category_path)

        return category_path

    def _write_page(self, file_path, page):
        file_path = '{path}.html'.format(
            path=os.path.join(self.output_path, *file_path),
        )

        _write_to_file(file_path, page)

    def _write_category(self, category):
        self._init_category(
            os.path.join(self.output_path, category.url_path)
        )

        category.load()
        for page in category.pages:
            if page.html:
                self._write_page([category.url_path, page.slug], page.html)

        for category in category.categories:
            self._write_category(category)

    def _render_sitemap(self):
        template = self.env.get_template('sitemap.html')
        file_path = os.path.join(self.output_path, 'static', 'sitemap.xml')
        site_map = template.render(
            pages=self.sitemap_links,
            base_url=self.base_url
        )

        _write_to_file(file_path, site_map)

    @property
    def sitemap_links(self):
        return []

    @property
    def navigation_links(self):
        links = [p for p in self.base.sub_pages if p.home_page]
        return sorted(links, key=lambda x: x.order)
