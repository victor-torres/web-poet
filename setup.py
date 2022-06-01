from setuptools import setup, find_packages


with open('README.rst') as f:
    long_description = f.read()


setup(
    name='web-poet',
    version='0.1.1',
    description="Zyte's Page Object pattern for web scraping",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='Scrapinghub',
    author_email='info@scrapinghub.com',
    url='https://github.com/scrapinghub/web-poet',
    packages=find_packages(
        exclude=(
            'tests',
        )
    ),
    install_requires=[
        'attrs >= 21.3.0',
        'parsel',
        'url-matcher',
        'multidict',
        'w3lib >= 1.22.0',
        'yarl',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
