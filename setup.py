from distutils.core import setup
setup(
    description='Static website Generator',
    name='staticpy',
    version='0.0.01',
    author='Todd Siflet',
    author_email='todd.siflet@gmail.com',
    packages=['staticpy'],
    entry_points={
        'console_scripts': [
            'staticpy-dev = staticpy.staticpy:develop',
            'staticpy-upload = staticpy.staticpy:upload_to_s3'
        ]
    },
    install_requires=[
        'jinja2',
        'watchdog',
        'boto',
    ],
)

