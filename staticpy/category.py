from __future__ import absolute_import

import os

from .page.base import BasePage
from .page.index import IndexPage

from .utils import (
    cached_property,
    ensure_directory_exists,
    list_directories,
    list_files,
)


class Category(object):
    _cache = None
    _page_size = 5

    def __init__(self, site, path):
        self.site = site
        self.path = path
        self.slug = os.path.split(path)[-1]

    def bust_cache(self):
        self._cache = None
        for category in self.categories:
            category.bust_cache()

    def write(self):
        ensure_directory_exists(
            os.path.join(self.site.output_path, self.url_path)
        )

        for page in self.index_pages:
            page.write()

        for page in self.children:
            page.write()

        for category in self.categories:
            category.write()

    @cached_property
    def index_page_count(self):
        return len(self.index_pages)

    @cached_property
    def sub_pages(self):
        pages = self.children + self.index_pages

        for category in self.categories:
            pages.extend(category.sub_pages)
        return pages

    @cached_property
    def child_template(self):
        return self.index.child_template or 'base.html'

    @cached_property
    def child_count(self):
        return len(self.children)

    @cached_property
    def categories(self):
        paths = [p for p in list_directories(self.path)]
        return [Category(self.site, p) for p in paths]

    @cached_property
    def url_path(self):
        parts = self.path.split(os.sep)
        parts = parts[parts.index('pages') + 1:]
        return '/'.join(parts)

    @cached_property
    def index(self):
        return self.index_pages[0]

    @cached_property
    def index_pages(self):
        indexes = []
        for n, pages in enumerate(self._paged_children):
            indexes.append(self._new_index_page(pages, n))
        if not indexes:
            indexes = [self._new_index_page([])]
        return indexes

    @cached_property
    def children(self):
        pages = self._generate_child_pages()
        if not self.site.include_drafts:
            pages = [p for p in pages if p.published]
        return sorted(pages, key=lambda x: x.order)

    @cached_property
    def _paged_children(self):
        for i in xrange(0, self.child_count, self._page_size):
            yield self.children[i:i+self._page_size]

    def _generate_child_pages(self):
        paths = (p for p in list_files(self.path)
                 if p.endswith('.page') and not p.endswith('index.page'))

        return [self._new_page(p) for p in paths]

    def _new_index_page(self, pages, page_number=0):
        path = os.path.join(self.path, 'index.page')
        return IndexPage(
            page_number,
            pages,
            path,
            self.url_path,
            self
        )

    def _new_page(self, path):
        return BasePage(path, self.url_path, self)

    def __getattr__(self, name):
        for category in self.categories:
            if category.slug == name:
                return category
        raise AttributeError
