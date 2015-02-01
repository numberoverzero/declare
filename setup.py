""" Setup file """
import os
import re
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.rst')).read()
# Remove custom RST extensions for pypi
CHANGES = re.sub(r'\(\s*:(issue|pr|sha):.*?\)', '', CHANGES)

REQUIREMENTS = [
]

TEST_REQUIREMENTS = [
    'pytest',
]

if __name__ == "__main__":
    setup(
        name='declare',
        version='0.6.0',
        description="Declarative scaffolding for frameworks",
        long_description=README + '\n\n' + CHANGES,
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Topic :: Software Development :: Libraries',
            'Topic :: Software Development :: Libraries :: Python Modules'
        ],
        author='Joe Cross',
        author_email='joe.mcross@gmail.com',
        url='http://declare.readthedocs.org/',
        license='MIT',
        keywords='meta metaclass declarative orm',
        platforms='any',
        include_package_data=True,
        py_modules=['declare'],
        packages=find_packages(exclude=('tests',)),
        install_requires=REQUIREMENTS,
        tests_require=REQUIREMENTS + TEST_REQUIREMENTS,
    )
