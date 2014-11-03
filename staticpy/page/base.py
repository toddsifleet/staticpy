from __future__ import absolute_import

import os

from ..utils import cached_property
from .reader import Reader
from .writer import Writer


def read_file(file_path):
    return Reader(file_path).read()


def write_page(page):
    return Writer(page).write()


class BasePage(object):
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
    def path(self):
        return self.url_path or 'home'

    @cached_property
    def no_render(self):
        return bool(self._get('url'))

    @cached_property
    def sitemap(self):
        return not self.no_sitemap and not self.no_render

    @cached_property
    def template_name(self):
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

    @property
    def order(self):
        order = self._get('order')
        if order:
            return int(order)
        return float('inf')

    def write(self):
        if not self.no_render:
            write_page(self)

    def __getattr__(self, name):
        return getattr(self._data, name)

    def _get(self, *args):
        return self._data.get(*args)

    @cached_property
    def _data(self):
        return read_file(self.file_path)

    @cached_property
    def _url(self):
        path_pieces = os.path.split(self.url_path.strip('\\/'))
        return '/' + '/'.join([x for x in path_pieces if x])
