import os
from os.path import isdir, join

from page import Page, ParentPage
from utils import cached_property


class Category(object):
    _cache = None

    def __init__(self, site, path):
        self.site = site
        self.path = path
        self.slug = os.path.split(path)[-1]

    def bust_cache(self):
        self._cache = None

    @cached_property
    def pages(self):
        pages = [p for p in self._list_dir() if p.endswith('.page')]
        pages = [self._new_page(p) for p in pages]
        if not self.site.include_drafts:
            pages = [p for p in pages if p.published]
        return pages

    @cached_property
    def categories(self):
        return [Category(self.site, p) for p in self._list_dir() if isdir(p)]

    def _list_dir(self):
        return [join(self.path, f) for f in os.listdir(self.path)]

    @cached_property
    def url_path(self):
        parts = self.path.split(os.sep)
        parts = parts[parts.index('pages') + 1:]
        return '/'.join(parts)

    @cached_property
    def index(self):
        for page in self.pages:
            if page.slug == 'index':
                return page

    @cached_property
    def children(self):
        pages = [p for p in self.pages if p.slug != 'index']
        return sorted(pages, key=lambda x: x.order)

    def _new_page(self, path):
        args = (path, self.url_path, self)
        if path.endswith('index.page'):
            return ParentPage(*args)
        return Page(*args)

    @cached_property
    def sub_pages(self):
        pages = self.pages[:]

        for category in self.categories:
            pages.extend(category.sub_pages)
        return pages

    @cached_property
    def child_template(self):
        return self.index.child_template or 'base.html'

    def __getattr__(self, name):
        for category in self.categories:
            if category.slug == name:
                return category
