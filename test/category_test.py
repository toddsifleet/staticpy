from os.path import join

from doubles import InstanceDouble

from staticpy.category import Category

dummy_site = lambda: InstanceDouble('staticpy.site.Site')


def test_url_path():
    c = Category(dummy_site(), join('pages', 'category'))
    assert c.url_path == 'category'
