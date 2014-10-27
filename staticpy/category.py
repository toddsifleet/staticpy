import os
from os.path import isdir

from page import Page
from index_page import IndexPage

from utils import (
    cached_property,
    ensure_directory_exists,
    list_directory,
)


class Category(object):
    _cache = None

    def __init__(self, site, path):
        self.site = site
        self.path = path
        self.slug = os.path.split(path)[-1]

    def _bust_cache(self):
        self._cache = None

    @cached_property
    def children(self):
        paths = (p for p in list_directory(self.path)
                 if p.endswith('.page') and not p.endswith('index.page'))

        pages = [self._new_page(p) for p in paths]
        if not self.site.include_drafts:
            pages = [p for p in pages if p.published]
        return sorted(pages, key=lambda x: x.order)

    @cached_property
    def children_chunks(self):
        n = 5  # temporarily hardcoded
        for i in xrange(0, self.child_count, n):
            yield self.children[i:i+n]

    @cached_property
    def child_count(self):
        return len(self.children)

    @cached_property
    def categories(self):
        return [Category(self.site, p) for p in list_directory(self.path)
                if isdir(p)]

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
        for n, pages in enumerate(self.children_chunks):
            indexes.append(self._new_index_page(pages, n))
        if not indexes:
            indexes = [self._new_index_page([])]
        return indexes

    def _new_index_page(self, pages, page_number=0):
        path = os.path.join(self.path, 'index.page')
        return IndexPage(
            page_number,
            pages,
            path,
            self.url_path,
            self
        )

    @cached_property
    def index_page_count(self):
        return len(self.index_pages)

    def _new_page(self, path):
        return Page(path, self.url_path, self)

    @cached_property
    def sub_pages(self):
        pages = self.children + [self.index]

        for category in self.categories:
            pages.extend(category.sub_pages)
        return pages

    @cached_property
    def child_template(self):
        return self.index.child_template or 'base.html'

    def write(self, output_path):
        ensure_directory_exists(
            os.path.join(output_path, self.url_path)
        )

        self._bust_cache()
        for page in self.index_pages:
            page.write(output_path)

        for page in self.children:
            page.write(output_path)

        for category in self.categories:
            category.write(output_path)

    def __getattr__(self, name):
        for category in self.categories:
            if category.slug == name:
                return category
