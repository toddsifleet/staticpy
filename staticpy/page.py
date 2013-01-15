import re
import os

def get_slug(file_path):
    #get the file name without the extension
    file_name = os.path.split(file_path)[-1].split('.')[0]
    slug = file_name.split('.')[0]
    return slug.replace('_', '-')

def build_url(path, slug):
    '''Format a url based on a slug and a file path

        Note: for pages with the slug index we omit the slug from the url

        returns: a url string
    '''
    #root directory means there is no path in the url
    if not path:
        #index means we can ignore the slug
        return '' if slug == 'index' else slug
    
    #we need to split and rejoin the url to account for different
    #file separators on windows
    path_pieces = os.path.split(path.strip('\\/'))
    url = '/'.join([x for x in path_pieces if x])
    return url if slug == 'index' else '%s/%s' % (url, slug)

class Page(object):
    '''Parses and stores a .page file 

        A .page file is a way to represent all of the data associate with a
        webpage, e.g. title, styles, content, etc.

        The format is:
            :<attribute-name>: <attribute-value>
            :<attribute-name>: 
                <multiline attribute-
                value>
            :<attribute-name>: <attribute-value>

        Each attribute in the specified file is stored as an attribute of the object, everything is 
        stored as a string.  These are designed to be passed into a templating engine.

        If you try to read an attribute that does not exist the Page object returns an empty string.
    '''

    #default here so we don't call int on an empty string
    order = '100'
    def __init__(self, file_path, url_path):
        '''Model a .page file as an object

            Read and parse .page file by default this sets: slug, url, path; these values
            are independent of the contents of the file.

            params:
                file_path: The complete path to the .page file:
                    e.g. /Users/toddsifleet/github/toddsifleet/dynamic/pages/projects/index.page
                url_path: the base url path to the page:
                    e.g. projects

        '''
        self.slug = get_slug(file_path)
        self.url = build_url(url_path, self.slug)
        self.path = url_path or 'home'
        self.parse(file_path)

    def parse(self, file_path):
        '''Parse a .page file_path

            Read a .page file and convert each of the attributes it defines
            into attributes of this object.  Values can be more than one line 
            the only rule is you can't start a line with :string: as this is what
            indicates a new attribute name

            params: file_path
        '''
        with open(file_path) as fp:
            lines = fp.readlines()

        attribute, value = '', ''
        name_regex = re.compile('^:(?P<attribute>[a-z\-_]+):\s*(?P<value>.*)$')
        for line in lines:
            data = name_regex.match(line) 
            if data:
                if value:
                    value = value.strip()
                    self.set(attribute, value)

                attribute = data.group('attribute')
                value = data.group('value')
            else:
                value += line
        self.set(attribute, value)

    def set(self, name, value):
        #clean up the attribute name/value before we store it
        name = name.strip().replace('-', '_')
        value = value.strip()
        setattr(self, name, value)

    def __getattr__(self, name):
        #don't die if we don't have a specified attribute
        try:
            return getattr(self, name)

        except:
            return ''