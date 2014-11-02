from doubles import allow, InstanceDouble, expect
from pytest import fixture

from staticpy.page.base import BasePage
from staticpy.page.data import Data


@fixture
def page(request):
    page = BasePage('file_path.page', 'url_path', dummy_category())
    allow(page)._data.and_return(Data())
    return page


def dummy_category():
    return InstanceDouble(
        'staticpy.category.Category',
        site=InstanceDouble('staticpy.site.Site'),
    )


def test_converts_order_to_an_int(page):
    allow(page)._data.and_return(Data(order='10'))

    assert page.order == 10


def test_order_defaults_to_infinity(page):
    assert page.order == float('inf')


def test_path_is_correct_if_there_is_no_url_path():
    page = BasePage('file_path', '', dummy_category())
    allow(page)._data.and_return(Data())

    assert page.path == 'home'


def test_path_is_correct_if_there_is_a_url_path(page):
    assert page.path == 'url_path'


def test_url_is_correct_for_index_page_with_no_url_path():
    page = BasePage('file_path', '', dummy_category())
    allow(page)._data.and_return(Data())

    assert page.url == '/file-path'


def test_url_is_correct_for_index_page_with_url_path(page):
    assert page.url == '/url_path/file-path'


def test_url_is_correct_for_multi_element_url_path():
    page = BasePage(
        'file_path',
        'url_path_1/url_path_2',
        dummy_category()
    )
    allow(page)._data.and_return(Data())

    assert page.url == '/url_path_1/url_path_2/file-path'


def test_reads_file_once_and_only_once():
    import staticpy.page.base
    page = BasePage('file_path', '', dummy_category())

    allow(staticpy.page.base).read_file.and_return(
        Data(foo='bar'),
    ).once()
    assert page.foo == 'bar'
    assert page.foo == 'bar'


def test_write_calls_write_page(page):
    import staticpy.page.base

    expect(staticpy.page.base).write_page.with_args(page).once()
    page.write()


def test_slug_replaces_underscores(page):
    assert page.slug == 'file-path'
