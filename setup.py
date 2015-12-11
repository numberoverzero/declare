""" Setup file """
import os
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()


def get_version():
    with open('declare.py') as f:
        for line in f:
            if line.startswith('__version__'):
                return eval(line.split('=')[-1])

REQUIREMENTS = [
]

TEST_REQUIREMENTS = [
    'pytest',
]

if __name__ == "__main__":
    setup(
        name='declare',
        version=get_version(),
        description="Declarative scaffolding for frameworks",
        long_description=README,
        classifiers=[
            'Development Status :: 4 - Beta',
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
        url='https://github.com/numberoverzero/declare',
        license='MIT',
        keywords='meta metaclass declarative',
        platforms='any',
        include_package_data=True,
        py_modules=['declare'],
        packages=find_packages(exclude=('tests',)),
        install_requires=REQUIREMENTS,
        tests_require=REQUIREMENTS + TEST_REQUIREMENTS,
    )
