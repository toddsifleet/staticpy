from distutils.core import setup
setup(
    description='Static website Generator',
    name='staticpy',
    version='0.0.01',
    author='Todd Siflet',
    author_email='todd.siflet@gmail.com',
    py_modules=['staticpy.staticpy'],
    entry_points={
        'console_scripts': [
            'staticpy = staticpy.staticpy:parse_args_and_run'
        ]
    }
)

