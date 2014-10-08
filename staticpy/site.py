import os

from jinja2 import Environment, PackageLoader

from page import Page
from utils import copy_attrs


def _write_to_file(fp, contents):
    with open(fp, 'w') as output:
        output.write(contents)


class Site(object):
    def __init__(self, settings, client_js_code=None, include_drafts=False):
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

        self.env = Environment(loader=PackageLoader('dynamic', 'templates'))
        self.base_template = self._load_template('base.html')
        self.parent_template = self._load_template('parent_base.html')

    def _get_pages(self):
        '''Get all page data

        Walks through the /site_path/dynamic/pages directory and parses
        each .page file into a page.Page object.

        sets self.page_tree to:
            {
                'index': Page(),
                'pages': [Page(), Page(), ...],
                'sub-categories': {
                    'name_1': {
                        index: Page(),
                        pages = [Page(), Page(), ...],
                        sub-categories:
                            ...
                    }
                }
            }
        '''
        pages_dir = os.path.join(self.input_path, 'dynamic', 'pages')
        category_dict = lambda: {
            'index': None,
            'pages': [],
            'sub-categories': {}
        }
        self.page_tree = category_dict()
        for (dir_path, dir_name, file_names) in os.walk(pages_dir):
            dir_path = dir_path[len(pages_dir) + 1::]
            category = self.page_tree
            for i in [x for x in os.path.split(dir_path) if x]:
                if i not in category['sub-categories']:
                    category['sub-categories'][i] = category_dict()
                category = category['sub-categories'][i]

            for file_name in [x for x in file_names if x.endswith('.page')]:
                file_path = os.path.join(pages_dir, dir_path, file_name)
                page = Page(file_path, dir_path)
                if not (self.include_drafts or page.published):
                    continue
                if not page.no_sitemap:
                    self.sitemap_links.append(page)
                if page.home_page:
                    self.navigation_links.append(page)
                if file_name == 'index.page':
                    category['index'] = page
                else:
                    category['pages'].append(page)

    def compile(self):
        '''Compile entire site_path

        -Parse all .page files
        -Builds and sorts the navigation_links
        -Renders and writes all pages to the output_path
        '''
        self.navigation_links = []
        self.sitemap_links = []
        self._get_pages()
        self.navigation_links.sort(key=lambda x: x.order)
        return self

    def save(self):
        self._render_pages(self.output_path, self.page_tree)
        self._render_sitemap()
        return self

    def _init_category(self, category_path):
        if not os.path.isdir(category_path):
            os.mkdir(category_path)

        return category_path

    def _render_page(self, page, template, **data):
        if page.template:
            template = self._load_template(page.template)

        return template.render(
            page=page,
            client_js_code=self.client_js_code,
            navigation_links=self.navigation_links,
            **data
        )

    def _write_page(self, file_path, page):
        '''Render and write a page

        Given a file_path, template, and page this renders the template
        with the pages data and writes the result to file_path

        params:
            file_path: path to write the resulting file
            template: a jinja2 template to use for rendering
            page: a page.Page object containing the pages data
            data <optional>: any additional data to pass into the template
        '''
        file_path = '{path}.html'.format(
            path=os.path.join(self.output_path, *file_path),
        )

        _write_to_file(file_path, page)

    def _render_pages(self, base_path, category):
        '''Render and write all pages

        Walks through self.page_tree and renders each page and writes
        the output to the appropriate file.

        This function calls it self recursively to make it through the entire
        page_tree each sub-categories entry is identical in form to
        self.page_tree so each sub-category can have as many of its own
        sub-categories as it chooses.

        params:
            base_path: the path the category we are working with
            category: a dictionary in the form of self.page_tree
        '''
        self._init_category(base_path)

        result = self._render_page(
            category['index'],
            self.parent_template,
            children=sorted(category['pages'], key=lambda x: int(x.order))
        )

        self._write_page([base_path, 'index'], result)

        for page in category['pages']:
            self._write_page(
                [base_path, page.slug],
                self._render_page(page, self.base_template),
            )

        for slug, category in category['sub-categories'].items():
            path = os.path.join(base_path, slug)
            self._render_pages(path, category)

    def _load_template(self, name):
        return self.env.get_template(name)

    def _render_sitemap(self):
        template = self._load_template('sitemap.html')
        file_path = os.path.join(self.output_path, 'static', 'sitemap.xml')
        site_map = template.render(
            pages=self.sitemap_links,
            base_url=self.base_url
        )

        _write_to_file(file_path, site_map)
