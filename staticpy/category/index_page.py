from __future__ import absolute_import

from ..page import Page
from ..utils import cached_property


class IndexPage(Page):
    def __init__(self, page_number, pages, *args, **kwargs):
        self.pages = pages
        self.page_number = page_number
        super(IndexPage, self).__init__(*args, **kwargs)

    @cached_property
    def template_name(self):
        return self._get('template', 'parent_base.html')

    @cached_property
    def url(self):
        url = '/' if not self.url_path else self._url
        if self.page_number:
            url = url + '/{}'.format(self.page_number)

        return url

    @cached_property
    def next(self):
        if self.page_number < self.category.index_page_count - 1:
            return self.category.index_pages[self.page_number+1]

    @cached_property
    def prev(self):
        if self.page_number:
            return self.category.index_pages[self.page_number-1]

    @cached_property
    def slug(self):
        if self.page_number:
            return str(self.page_number)
        return 'index'

    @cached_property
    def include_in_navigation(self):
        if not self._get('include_in_navigation'):
            return False
        else:
            return not self.page_number
