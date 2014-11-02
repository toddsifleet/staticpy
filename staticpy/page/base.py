from __future__ import absolute_import

import os

from jinja2 import Environment, PackageLoader

from ..utils import cached_property, write_to_file
from .reader import Reader


class BasePage(object):
    _data = None
    _env = None
    _cache = None

    def __init__(
        self,
        file_path,
        url_path,
        category,
    ):
        self.site = category.site
        self.category = category
        self.file_path = file_path
        self.url_path = url_path
        self.reader = Reader(file_path)

    @cached_property
    def _data(self):
        return self.reader.read()

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
            return '/' + self.slug

        url = self._url
        return '%s/%s' % (url, self.slug)

    @cached_property
    def _url(self):
        path_pieces = os.path.split(self.url_path.strip('\\/'))
        return '/' + '/'.join([x for x in path_pieces if x])

    @cached_property
    def path(self):
        return self.url_path or 'home'

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
        return bool(self._get('url'))

    @cached_property
    def sitemap(self):
        return not self.no_sitemap and not self.no_render

    @cached_property
    def template(self):
        if not self._env:
            self._env = Environment(
                loader=PackageLoader('dynamic', 'templates')
            )
        return self._env.get_template(self._template_name)

    @cached_property
    def _template_name(self):
        return self._get(
            'template',
            self.category.child_template,
        )

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

    def write(self, file_path):
        if self.no_render:
            return

        file_path = '{path}.html'.format(
            path=os.path.join(
                file_path,
                self.category.url_path,
                self.slug
            ),
        )

        write_to_file(file_path, self.html)

    def __getattr__(self, name):
        return getattr(self._data, name)

    def _get(self, *args):
        return self._data.get(*args)
