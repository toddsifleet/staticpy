from __future__ import absolute_import

import os

from ..utils import ensure_directory_exists


def _create_category_directories(output_path, categories):
    for category in categories:
        ensure_directory_exists(
            os.path.join(output_path, category.url_path)
        )


class Writer(object):
    def __init__(self, site, output_path):
        self.site = site
        self.output_path = output_path

    def write(self):
        _create_category_directories(
            self.output_path,
            self.site.categories,
        )

        for page in self.site.pages:
            page.write()

        self.site.sitemap.write()
