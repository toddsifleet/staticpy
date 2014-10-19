import re
import os
import datetime

from jinja2 import Environment, PackageLoader

from utils import cached_property


def _read_file(path):
    with open(path) as fp:
        return fp.readlines()


def _parse_file(path):
    '''Parse a .page file_path

    Read a .page file and convert each of the attributes it defines
    into attributes of this object.  Values can be more than one line
    the only rule is you can't start a line with :string: as this is what
    indicates a new attribute name

    params: path
    '''
    output = {}

    attribute, value = '', ''
    name_regex = re.compile('^:(?P<attribute>[a-z\-_]+):\s*(?P<value>.*)$')
    for line in _read_file(path):
        data = name_regex.match(line)
        if data:
            if value:
                output[attribute] = value.strip()

            attribute = data.group('attribute')
            value = data.group('value')
        else:
            value += "\n" + line.strip()
    output[attribute] = value.strip()
    return output


class Page(object):
    '''Parses and stores a .page file

    A .page file is a way to represent all of the data associate with a
    webpage, e.g. title, styles, content, etc.

    The format is:
        :<attribute-name>: <attribute-value>
        :<attribute-name>:
            <multiline attribute-
            value>
        :<attribute-name>: <attribute-value>

    Each attribute in the specified file is stored as an attribute of the
    object, everything is stored as a string.  These are designed to be
    passed into a templating engine.

    If you try to read an attribute that does not exist the Page object
    returns an empty string.
    '''

    def __init__(
        self,
        file_path,
        url_path,
        category,
    ):
        '''Model a .page file as an object

        Read and parse .page file by default this sets: slug, url, path;
        these values are independent of the contents of the file.

        params:
            file_path: The complete path to the .page file:
                e.g. /path/to/site/dynamic/pages/projects/index.page
            url_path: the base url path to the page:
                e.g. projects

        '''
        self._data = {}
        self._env = None

        self.site = category.site
        self.category = category
        self.file_path = file_path
        self.url_path = url_path
        self._cache = None

        self.load()

    def load(self):
        attrs = _parse_file(self.file_path)
        for k, v in attrs.items():
            self.set(k, v)

    def set(self, name, value):
        name = name.strip().replace('-', '_')
        self._data[name] = value.strip()

    def __getattr__(self, name):
        return self._get(name, '')

    def _to_list(self, name):
        lines = self._get(name, '').split('\n')
        return [x.strip() for x in lines]

    @cached_property
    def slug(self):
        file_name = os.path.split(self.file_path)[-1].split('.')[0]
        slug = file_name.split('.')[0]
        return slug.replace('_', '-')

    @cached_property
    def url(self):
        if self._get('url'):
            return self._get('url')
        elif not self.url_path:
            return '/' if self.slug == 'index' else '/' + self.slug

        path_pieces = os.path.split(self.url_path.strip('\\/'))
        url = '/' + '/'.join([x for x in path_pieces if x])
        return url if self.slug == 'index' else '%s/%s' % (url, self.slug)

    @cached_property
    def last_modified(self):
        seconds = os.path.getmtime(self.file_path)
        return datetime.datetime.fromtimestamp(seconds)

    @cached_property
    def path(self):
        return self.url_path or 'home'

    @cached_property
    def order(self):
        return int(self._get('order', 100))

    @cached_property
    def js_imports(self):
        return self._to_list('js_imports')

    @cached_property
    def css_imports(self):
        return self._to_list('css_imports')

    @cached_property
    def html(self):
        return self._html()

    def _html(self, **data):
        if self.no_render:
            return None

        return self.template.render(
            page=self,
            category=self.category,
            navigation_links=self.site.navigation_links,
            client_js_code=self.site.client_js_code,
            **data
        )

    @cached_property
    def no_render(self):
        return self._get('url')

    @cached_property
    def template(self):
        if not self._env:
            self._env = Environment(
                loader=PackageLoader('dynamic', 'templates')
            )
        return self._env.get_template(self._template_name)

    @cached_property
    def _template_name(self):
        name = self._get('template')
        if not name:
            if self.slug == 'index':
                name = 'parent_base.html'
            else:
                name = self.category.child_template
        return name

    @cached_property
    def prev(self):
        prev_page = None
        for p in self.category.children:
            if p == self:
                return prev_page
            prev_page = p

    @cached_property
    def next(self):
        found = False
        for p in self.category.children:
            if found:
                return p
            found = p == self

    def _get(self, key, default=None):
        return self._data.get(key, default)

class ParentPage(Page):

    @cached_property
    def html(self):
        return self._html(children=self.category.children)

    @cached_property
    def children(self):
        return self.category.children
