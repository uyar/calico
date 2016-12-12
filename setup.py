from setuptools import setup


setup(
    name='pace',
    version='1.0a1',
    description='Programming assignment checker.',
    long_description='',
    url='https://bitbucket.org/uyar/pace',
    author='H. Turgut Uyar',
    author_email='uyar@itu.edu.tr',
    license='GPL',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='cli test',
    py_modules=['pace'],
    install_requires=['pexpect', 'rsonlite'],
    entry_points="""
        [console_scripts]
        pace=pace:main
    """
)
