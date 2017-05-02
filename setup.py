from setuptools import setup


setup(
    name='pace',
    version='1.0a2',
    description='Programming assignment checker and evaluator.',
    long_description='',
    url='https://bitbucket.org/uyar/pace',
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
    keywords='cli testing programming assignment',
    py_modules=['pace'],
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
        pace=pace:main
    """
)
