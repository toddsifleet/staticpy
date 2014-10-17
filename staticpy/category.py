import os
from os.path import isdir, join

from page import Page, ParentPage


class Category(object):
    def __init__(self, site, path):
        self.site = site
        self.path = path

    @property
    def pages(self):
        pages = [p for p in self._list_dir() if p.endswith('.page')]
        return [self._new_page(p) for p in pages]

    @property
    def categories(self):
        return [Category(self.site, p) for p in self._list_dir() if isdir(p)]

    def _list_dir(self):
        return [join(self.path, f) for f in os.listdir(self.path)]

    @property
    def url_path(self):
        parts = self.path.split(os.sep)
        parts = parts[parts.index('pages') + 1:]
        return '/'.join(parts)

    @property
    def index(self):
        for page in self.pages:
            if page.slug == 'index':
                return page

    def _new_page(self, path):
        args = (path, self.url_path, self)
        if path.endswith('index.page'):
            return ParentPage(*args)
        return Page(*args)

    @property
    def sub_pages(self):
        pages = self.pages[:]

        for category in self.categories:
            pages.extend(category.sub_pages)
        return pages
