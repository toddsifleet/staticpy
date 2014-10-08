import os

import staticpy.site
from staticpy.utils import load_settings


def settings():
    path = os.path.realpath(__file__)
    parts = path.split(os.sep)[:-2]
    parts.append('template')
    path = os.path.join(*parts)
    #  '/' is a temporary hack
    return load_settings('/' + path)


class TestCompilingSite(object):
    def setup_method(self, method):
        self.settings = settings()
        self.site = staticpy.site.Site(self.settings).compile()

    def test_site_index(self):
        page = self.site.page_tree['index']
        assert page.title == 'home'
        assert page.published

    def test_sub_page_index(self):
        category = self.site.page_tree['sub-categories']['category']
        page = category['index']
        assert page.title == 'Category'
        assert len(category['pages']) == 1
        assert page.published

    def test_sub_page(self):
        page = self.site.page_tree['sub-categories']['category']['pages'][0]
        assert page.title == 'A Sub Page'
        assert page.published


class TestWritingSite(object):
    """Haven't decied how to tes this"""
    def setup_method(self, method):
        self.settings = settings()
        self.site = staticpy.site.Site(self.settings).compile()

    def test_site_index(self):
        pass

    def test_sub_page_index(self):
        pass

    def test_sub_page(self):
        pass
