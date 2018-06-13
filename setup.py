import os
import re
import setuptools

p = os.path.dirname(os.path.abspath(__file__))

def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)

version = get_version('simple_lock')

setuptools.setup(
    name="simple_lock",
    version=version,
    python_requires='>=3.6.5',    
    author="Koji Ono",
    author_email="kbu94982@gmail.com",
    description="Simple Lockfile System.",
    url='https://github.com/0h-n0/simple-lock',
    long_description=open(os.path.join(p, 'README.md')).read(),
    packages=setuptools.find_packages(),
    install_requires=['requests'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest-cov', 'pytest-html', 'pytest', 'codecov'],
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],
)
