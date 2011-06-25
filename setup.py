from distutils.core import setup

with open('README') as file:
    long_description = file.read()

setup(
    name='gtkchartlib',
    version='0.1.2',
    description='Collection of GTK+ chart widgets',
    author='Fraser Tweedale',
    author_email='frase@frase.id.au',
    url='https://gitorious.org/gtkchartlib',
    packages=['gtkchartlib'],
    data_files=[
        (
            'doc/gtkchartlib/demo',
            ['demo/ringchart.py', 'demo/ringchart_single_toplevel.py']
        ),
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Widget Sets',
    ],
    long_description=long_description,
)
