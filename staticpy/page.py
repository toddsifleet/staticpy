import re
import os
import datetime

from jinja2 import Environment, PackageLoader


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
        navigation_links=None,
        client_js_code=None
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
        self.data = {}
        self._env = None
        self.children = []

        self.navigation_links = navigation_links
        self.client_js_code = client_js_code
        self.file_path = file_path
        self.url_path = url_path

        self.load()

    def load(self):
        attrs = _parse_file(self.file_path)
        for k, v in attrs.items():
            self.set(k, v)

    def set(self, name, value):
        name = name.strip().replace('-', '_')
        self.data[name] = value.strip()

    def __getattr__(self, name):
        return self.data.get(name, '')

    def _to_list(self, name):
        lines = self.data.get(name, '').split('\n')
        return [x.strip() for x in lines]

    @property
    def slug(self):
        file_name = os.path.split(self.file_path)[-1].split('.')[0]
        slug = file_name.split('.')[0]
        return slug.replace('_', '-')

    @property
    def url(self):
        if not self.url_path:
            return '' if self.slug == 'index' else self.slug

        path_pieces = os.path.split(self.url_path.strip('\\/'))
        url = '/'.join([x for x in path_pieces if x])
        return url if self.slug == 'index' else '%s/%s' % (url, self.slug)

    @property
    def last_modified(self):
        seconds = os.path.getmtime(self.file_path)
        return datetime.datetime.fromtimestamp(seconds)

    @property
    def path(self):
        return self.url_path or 'home'

    @property
    def order(self):
        return int(self.data.get('order', 100))

    @property
    def js_imports(self):
        return self._to_list('js_imports')

    @property
    def css_imports(self):
        return self._to_list('css_imports')

    @property
    def html(self):
        return self.template.render(
            page=self,
            navigation_links=self.navigation_links,
            client_js_code=self.client_js_code,
            children=sorted(self.children, key=lambda x: x.order),
        )

    @property
    def template(self):
        name = self.data.get('template')
        if not name:
            if self.slug == 'index':
                name = 'parent_base.html'
            else:
                name = 'base.html'
        return self._load_template(name)

    def _load_template(self, name):
        if not self._env:
            self._env = Environment(
                loader=PackageLoader('dynamic', 'templates')
            )
        return self._env.get_template(name)
