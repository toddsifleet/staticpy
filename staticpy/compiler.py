import os
import shutil

from page import Page

#dependency, this is our templating engine
from jinja2 import Template, Environment, PackageLoader

class Site(object):
    def __init__(self, input_path, output_path, dev_server = None):
        self.dev_server = dev_server
        self.input_path = input_path
        self.output_path = output_path
        self.navigation_links = []

    def get_pages(self):
        pages_dir = os.path.join(self.input_path, 'dynamic', 'pages')
        category_dict = lambda: { 'index': None, 'pages': [], 'sub-categories': {} }
        self.page_tree = category_dict() #this keeps track of the page hierarchy
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
                if page.home_page:
                    self.add_to_navigation(page)
                if file_name == 'index.page':
                    category['index'] = page
                else:
                    category['pages'].append(page)

    def add_to_navigation(self, page):
        self.navigation_links.append({
            'title': page.title,
            'url': page.url,
            'order': page.order or 1000
        })

    def compile(self):
        self.get_pages()
        self.navigation_links.sort(key = lambda x: int(x['order']))
        self.render_pages(self.output_path, self.page_tree)

    def init_category(self, category_path):
        if not os.path.isdir(category_path):
            os.mkdir(category_path)

        return category_path

    def write_file(self, file_path, template, page, data = None):
        if data is None:
            data = {}
        file_path = os.path.join(self.output_path, *file_path)
        file_path = '%s.html' % file_path
        
        page.file_path = file_path
        with open(file_path, 'w') as out:
            page = template.render(
                page = page,
                dev_server = self.dev_server,
                navigation_links = self.navigation_links,
                **data
            )
            out.write(page)

    def render_pages(self, base_path, category):
        #we need to reload incase a template changed
        env = Environment(loader = PackageLoader('dynamic', 'templates'))
        base_template = env.get_template('base.html')
        parent_template = env.get_template('parent_base.html')
        page = category['index']
        template =  env.get_template(page.template) if page.template else parent_template
        self.write_file([base_path, 'index'], template, page, {
            'children': sorted(category['pages'], key = lambda x: int(x.order))
        })

        for page in category['pages']:
            template =  env.get_template(page.template) if page.template else base_template
            self.write_file([base_path, page.slug], template, page)

        for slug, category in category['sub-categories'].items():
            path = os.path.join(base_path, slug)
            self.init_category(path)
            self.render_pages(os.path.join(base_path, slug), category)