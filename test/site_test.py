import os

from pytest import fixture
from doubles import expect, allow

import staticpy.site
from staticpy.utils import load_settings


def get_settings():
    path = os.path.realpath(__file__)
    parts = path.split(os.sep)[:-2]
    parts.append('template')
    path = os.path.join(*parts)
    #  '/' is a temporary hack
    return load_settings('/' + path)


@fixture
def site(request):
    site = staticpy.site.Site(get_settings())
    allow(site.sitemap).write
    return site


class TestInit(object):
    def test_attrs_are_copied_from_settings(self, site):
        settings = get_settings()
        assert site.input_path == settings.input_path
        assert site.output_path == settings.output_path
        assert site.base_url == settings.base_url

    def test_client_js_code(self, site):
        assert site.client_js_code == ''

    def test_incldue_drafts(self, site):
        assert not site.include_drafts


class TestSave(object):
    def test_calls_write_on_each_page(self, site):
        for page in site.pages:
            expect(page).write
        site.save()

    def test_renders_sitemap(self, site):
        for page in site.pages:
            allow(page).write
        expect(site.sitemap).write
        site.save()
