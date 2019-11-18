import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

setup(
    name='imagestore-mitoc',
    version='4.0.0',
    packages=find_packages(),
    install_requires=[
        'django>=1.11',
        'pillow',
        'sorl-thumbnail>=12.4.0',
        'django-autocomplete-light',
        'django-tagging',
        'swapper',
        'chardet',
    ],
    author='Haiyan Xu',
    author_email='haiyanxuu@gmail.com',
    description='forked from hovel/imagestore... imagestore version for use with MITOC photo gallery',
    long_description=README,
    license='GPL',
    keywords='django gallery',
    url='https://github.com/haiyanxu/imagestore-mitoc',
    include_package_data=True
)
