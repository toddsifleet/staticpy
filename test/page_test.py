from doubles import expect, allow

import staticpy.page


def mock_file(*lines):
    lines = [x + '\n' for x in lines]
    allow(staticpy.page)._read_file.and_return(lines)


def test_parses_file_on_initialization():
    expect(staticpy.page)._parse_file.with_args('foobar').and_return({})

    staticpy.page.Page('foobar', 'url_path')


def test_converts_order_to_an_int():
    mock_file(':order: 10')
    page = staticpy.page.Page('file_path', 'url_path')

    assert page.order == 10


def test_converts_js_imports_to_list():
    mock_file(':js_imports:', 'import 1', 'import 2')
    page = staticpy.page.Page('file_path', 'url_path')

    assert page.js_imports == ['import 1', 'import 2']


def test_converts_css_imports_to_list():
    mock_file(':css_imports:', 'import 1', 'import 2')
    page = staticpy.page.Page('file_path', 'url_path')

    assert page.css_imports == ['import 1', 'import 2']


def test_path_is_correct_if_there_is_no_url_path():
    mock_file()
    page = staticpy.page.Page('file_path', '')

    assert page.path == 'home'


def test_path_is_correct_if_there_is_a_url_path():
    mock_file()
    page = staticpy.page.Page('file_path', 'url_path')

    assert page.path == 'url_path'


def test_single_line_attributes():
    mock_file(':attr_name: attr_value')
    page = staticpy.page.Page('file_path', 'url_path')

    assert page.attr_name == 'attr_value'


def test_multi_line_attributes():
    mock_file(':attr_name: attr_value_1', 'attr_value_2')
    page = staticpy.page.Page('file_path', 'url_path')

    assert page.attr_name == 'attr_value_1\nattr_value_2'


def test_url_is_correct_for_index_page_with_no_url_path():
    mock_file()
    page = staticpy.page.Page('file_path', '')

    assert page.url == 'file-path'


def test_url_is_correct_for_index_page_with_url_path():
    mock_file()
    page = staticpy.page.Page('file_path', 'url_path')

    assert page.url == 'url_path/file-path'


def test_url_is_correct_for_multi_element_url_path():
    mock_file()
    page = staticpy.page.Page('file_path', 'url_path_1/url_path_2')

    assert page.url == 'url_path_1/url_path_2/file-path'