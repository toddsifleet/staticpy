A python static site generator
=============

I wanted a simple way to generate a personal static website, this is what I got.  Some of the features:

-It uses the [Jinja](http://jinja.pocoo.org/) templating engine

-It has a built in development server, that reloads on file changes.

-It has built in support to upload to s3.

Site Structure:
-------

	/dynamic
		/templates
			base.html
			parent_base.html
		/pages
			index.page
			/category
				/index.page
				/sub_page_1.page
			/page_1.page
	/static
	
Define Page Data:
-------
Pages can have any attribute defined on them, only: template, order, published, and url are treated different.  All attributes defined in the .page file are passed into the appropriate template. 

	:order: Order in navigation links.
	:published: Only deploy pages with this flag.
	:url: This page is not rendered, it is just a link to a page on another site. 
	:attr-name[list]: Attributes with [list] will be interpreted as a list, one item per .
	:template: Overrided the default template. 

Define Templates:
-------

Templates live in the dynamic/templates directory. By default the template is base.html for standard pages, and parent_base.html for parent pages.  This can be overwritten by defining :template in the .page file. 

Then what?
-------
All of the information is part out of the above file (*.page), and put into an object that can be passed into a jinja template.  Your page structure is defined by how you store your files on your hard drive.  e.g

	yoursite.com: /input/path/web_site/index.page
	yoursite.com/about: /input/path/web_site/about.page
	yoursite.com/blog/static-site: /input/path/web_site/static_site.page

These files are then compile into your output path in the form:

	/user/web_site/index.page -> output/path/index.html
	/user/web_site/about.page -> output/path/about.html
	/user/web_site/blog/static_site.page -> output/path/blog/static_site.html

Using the dev server these pages are visible at:

	localhost:8080
	localhost:8080/about
	localhost:8080/blog/static_site

Usage:
-------
	
	# development mode
	>> staticpy-dev /path/to/site
	
	# upload your site
	>> staticpy-upload /path/to/site

License:
-------

See LICENSE
