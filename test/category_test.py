from doubles import InstanceDouble, allow
from pytest import fixture

from staticpy.category import Category


def dummy_page(order=0, published=True, **kwargs):

    return InstanceDouble(
        'staticpy.page.Page',
        order=order,
        published=published,
        **kwargs
    )


def dummy_pages(count=10, **kwargs):
    return [dummy_page(**kwargs) for c in range(count)]


@fixture
def site(request):
    return InstanceDouble('staticpy.site.Site')


@fixture
def category(request):
    return Category(
        InstanceDouble('staticpy.site.Site', include_drafts=True),
        'pages/category',
    )


class TestInit(object):
    def test_url_one_level_deep(self):
        c = Category(None, 'pages/category')
        assert c.url_path == 'category'

    def test_url_two_levels_deep(self):
        c = Category(None, 'pages/bob/barker')
        assert c.url_path == 'bob/barker'

    def test_site(self, site):
        c = Category(site, '')
        assert c.site == site

    def test_slug(self):
        c = Category(None, 'bob/barker')
        assert c.slug == 'barker'


class TestChildren(object):
    def test_returns_an_ordered_list_of_pages(self, category):
        allow(category)._generate_child_pages.and_return([
            dummy_page(slug='page-1', order=10),
            dummy_page(slug='page-2', order=0),
        ])

        pages = category.children
        assert pages[0].slug == 'page-2'
        assert pages[1].slug == 'page-1'

    def test_caches_result(self, category):
        allow(category)._generate_child_pages.and_return(
            [dummy_page(slug='page-1')],
            None,
        )
        original = category.children
        assert original is category.children

    def test_bust_cache(self, category):
        allow(category)._generate_child_pages.and_return(
            [dummy_page(slug='page-1')],
            [dummy_page(slug='page-2')],
        )
        allow(category).categories.and_return([])

        original = category.children
        category.bust_cache()
        assert category.children is not original
        assert category.children[0].slug == 'page-2'

    def test_returns_drafts_if_include_drafts(self, category):
        category.site.include_drafts = True
        allow(category)._generate_child_pages.and_return(
            [dummy_page(slug='page-1', published=False)],
        )
        assert category.children[0].slug == 'page-1'

    def test_does_not_returns_drafts_if_not_include_drafts(self, category):
        category.site.include_drafts = False
        allow(category)._generate_child_pages.and_return([
            dummy_page(slug='page-1', published=False),
            dummy_page(slug='page-2', published=True),
        ])
        assert category.children[0].slug == 'page-2'


class TestUrlPath(object):
    def test_single_element_path(self, category):
        assert category.url_path == 'category'

    def test_multi_element_path(self):
        category = Category(
            InstanceDouble('staticpy.site.Site'),
            'pages/bob/barker',
        )
        assert category.url_path == 'bob/barker'


class TestIndexPages(object):
    def test_index(self, category):
        pages = dummy_pages()
        allow(category).children.and_return(pages)

        assert category.index.pages == pages[:category._page_size]

    def test_index_2(self, category):
        pages = dummy_pages()
        allow(category).children.and_return(pages)
        index = category.index_pages[1]

        assert index.pages == pages[category._page_size:]


class TestSubCategories(object):
    def test_empty_list(self, category):
        allow(category).categories.and_return([])
        assert category.sub_categories == []

    def test_one_level_deep(self, category):
        category_2 = Category(category.site, 'pages/category/category_2')
        category.categories = [category_2]
        category_2.categories = []

        assert category.sub_categories == [category_2]

    def test_multiple_levels_deep(self, category):
        category_2 = Category(category.site, 'pages/category/category_2')
        category_3 = Category(category.site, 'pages/category/category_3')
        category.categories = [category_2]
        category_2.categories = [category_3]
        category_3.categories = []

        assert category.sub_categories == [category_2, category_3]
