from setuptools import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

setup(
    name='calico',
    version='1.0a2',
    description='I/O checker for command-line programs.',
    long_description=readme + '\n\n' + history,
    url='https://bitbucket.org/uyar/calico',
    author='H. Turgut Uyar',
    author_email='uyar@itu.edu.tr',
    license='GPL',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Education',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.4',
        'Topic :: Education :: Testing',
        'Topic :: Utilities'
    ],
    keywords='cli testing',
    py_modules=['calico'],
    install_requires=['pexpect', 'ruamel.yaml'],
    extras_require={
        'dev': [
            'flake8',
            'mypy'
        ],
        'doc': [
            'sphinx',
            'sphinx_rtd_theme'
        ],
        'test': [
            'pytest',
            'pytest-cov'
        ],
    },
    entry_points="""
        [console_scripts]
        calico=calico:main
    """
)
