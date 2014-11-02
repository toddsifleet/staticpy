from __future__ import absolute_import

import os

from .category import Category
from .page.sitemap import Sitemap
from .utils import copy_attrs, cached_property


class Site(object):
    _cache = None

    def __init__(self, settings, client_js_code='', include_drafts=False):
        '''A staticpy Site Object

        params:
            settings: an object defining
                - input_path: the full directory to the websites files
                - output_path: where you want the resulting files to go
                - base_url: the url where your website is hosted
            client_js_code: A piece of JS to communicate with the server
            include_drafts: Include pages that have not been published

        '''
        copy_attrs(self, settings, 'input_path', 'output_path', 'base_url')

        self.client_js_code = client_js_code
        self.include_drafts = include_drafts

    def save(self):
        self.base.write()
        self.sitemap.write()
        return self

    def recompile(self):
        self.base.bust_cache()
        self.save()

    @cached_property
    def sitemap_links(self):
        return [p for p in self.pages if p.sitemap]

    @cached_property
    def navigation_links(self):
        links = [p for p in self.pages if p.include_in_navigation]
        return sorted(links, key=lambda x: x.order)

    @cached_property
    def pages(self):
        return [p for p in self.base.sub_pages if p]

    @cached_property
    def base(self):
        return Category(
            self,
            os.path.join(self.input_path, 'dynamic', 'pages'),
        )

    @cached_property
    def sitemap(self):
        return Sitemap(self)
