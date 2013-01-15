A python static site generator
=============

I wanted a simple way to generate a personal static website, this is what I got.  Some of the features:

-It uses the powerful [Jinja Template](http://jinja.pocoo.org/)

-It has a built in development server, that reloads on file changes.

-The pages automatically refresh on saves so you see the effects of your changes without switching windows.  We insert a little snippet of javascript that is connect via websocket to know when a file has changed.  This makes iteration incredibly fast.

-It has built in support to upload to s3.

More to come, I am still working on this!
=============

What does a page's data look like
-------
	:html-title: Html title
	:heading: Page Heading
	:title: Nav Title
	:home_page: Display on the home page?
	:template: Non Default Template
	:order: Order in nav bar
	:meta-description:
	:meta-keywords:
	:styles:
		Style specific to this page
	:scripts:
		Scripts specific to this page
	:content:
		The main content

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
	localhost:8080/blog/static_site.page

More to come...
======

License:
-------

See LICENSE
