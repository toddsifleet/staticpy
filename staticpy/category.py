import os
from os.path import isdir, join

from page import Page, ParentPage


class Category(object):
    def __init__(self, site, path):
        self.site = site
        self.path = path
        self._pages = None

    def load(self):
        pages = [p for p in self._list_dir() if p.endswith('.page')]
        pages = [self._new_page(p) for p in pages]
        if not self.site.include_drafts:
            pages = [p for p in pages if p.published]
        self._pages = pages

    @property
    def pages(self):
        if self._pages is None:
            self.load()
        return self._pages

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

    @property
    def children(self):
        pages = [p for p in self.pages if p.slug != 'index']
        return sorted(pages, key=lambda x: x.order)

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

    @property
    def child_template(self):
        return self.index.child_template or 'base.html'
