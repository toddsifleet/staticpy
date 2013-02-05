import os
import shutil

from page import Page

#dependency, this is our templating engine
from jinja2 import Template, Environment, PackageLoader

class Site(object):
    '''A class to represent an entire site

        This class represents and compiles a collection of .page files which
        represents an entire website.  The url paths match the file structure of
        your website's directory.

        A website directory should be in the form
            parent_dir:
                dynamic: 
                    templates: jinja2 templates
                    pages: 
                        index.page
                        ...
                        sub_category:
                            index.page
                            page1.page
                            ...
                            sub_category:
                                index.page
                                ...
                static:
                    files to be copied to the output_path/static
                settings.py
                    aws_keys = ('access_key', 'private_key')
                    s3_bucket = 'bucket_name'
    '''
    def __init__(self, input_path, output_path, client_js_code = None):
        '''Initialize a website

            params:
                input_path: the full directory to the websites files (.page, templates)
                output_path: where you want the resulting files to go
                self.client_js_code: A piece of JS to communicate with the websocket server
        '''
        self.client_js_code = client_js_code
        self.input_path = input_path
        self.output_path = output_path
        self.navigation_links = []

    def get_pages(self):
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
            params:
                None
            return:
                None
        '''
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
        #add a Page() object to self.navigation_links
        self.navigation_links.append({
            'title': page.title,
            'url': page.url,
            'order': page.order or 1000
        })

    def compile(self):
        '''Compile entire site_path

            -Parse all .page files
            -Builds and sorts the navigation_links
            -Renders and writes all pages to the output_path

            params:
                None
            return:
                None
        '''
        self.get_pages()
        self.navigation_links.sort(key = lambda x: int(x['order']))
        self.render_pages(self.output_path, self.page_tree)

    def init_category(self, category_path):
        #creates a category directory if it doesn't exist
        if not os.path.isdir(category_path):
            os.mkdir(category_path)

        return category_path

    def write_file(self, file_path, template, page, data = None):
        '''Render and write a page

            Given a file_path, template, and page this renders the template
            with the pages data and writes the result to file_path

            params:
                file_path: path to write the resulting file
                template: a jinja2 template to use for rendering
                page: a page.Page object containing the pages data
                data <optional>: any additional data to pass into the template
            returns:
                nothing
        '''
        if data is None:
            data = {}
        file_path = os.path.join(self.output_path, *file_path)
        file_path = '%s.html' % file_path
        
        page.file_path = file_path
        with open(file_path, 'w') as out:
            page = template.render(
                page = page,
                client_js_code = self.client_js_code,
                navigation_links = self.navigation_links,
                **data
            )
            out.write(page)

    def render_pages(self, base_path, category):
        '''Render and write all pages

            Walks through self.page_tree and renders each page and writes
            the output to the appropriate file.

            This function calls it self recursively to make it through the entire page_tree
            each sub-categories entry is identical in form to self.page_tree so each sub-category
            can have as many of its own sub-categories as it chooses.
            
            params:
                base_path: the path the category we are working with
                category: a dictionary in the form of self.page_tree
            returns:
                none

        '''
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
            self.render_pages(path, category)