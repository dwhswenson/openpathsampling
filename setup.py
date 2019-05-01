"""OpenPathSampling: A python package to do path sampling simulations

OpenPathSampling (http://github.com/choderalab/openpathsampling) is a
python library to do transition interface sampling.
"""

from __future__ import print_function
from builtins import str
from setuptools import setup
import sys
import os
import subprocess

# experimental yaml support to read the settings
# import yaml

sys.path.insert(0, '.')


def trunc_lines(s):
    parts = s.split('\n')
    while len(parts[0]) == 0:
        parts = parts[1:]

    while len(parts[-1]) == 0:
        parts = parts[:-1]

    parts = [part for part in parts if len(part) > 0]

    return ''.join(parts)


# +-----------------------------------------------------------------------------
# | GET GIT VERSION
# +-----------------------------------------------------------------------------

def get_git_version():
    # Return the git revision as a string
    # copied from numpy setup.py
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {}
        for k in ['SYSTEMROOT', 'PATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v

        # LANGUAGE is used on win32
        env['LANGUAGE'] = 'C'
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        output = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, env=env).communicate()[0]
        return output

    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        git_revision = out.strip().decode('ascii')
    except OSError:
        git_revision = 'Unknown'

    return git_revision


# +-----------------------------------------------------------------------------
# | WRITE version.py FILE
# +-----------------------------------------------------------------------------

def write_version_py(
        prefs,
        filename='openpathsampling/version.py',
):
    cnt = """
# This file is automatically generated by setup.py
short_version = '%(version)s'
version = '%(version)s'
full_version = '%(full_version)s'
git_revision = '%(git_revision)s'
release = %(isrelease)s

if not release:
    version = full_version
"""

    # Adding the git rev number needs to be done inside write_version_py(),
    # otherwise the import of numpy.version messes up the build under Python 3.
    if os.path.exists('.git'):
        git_version = get_git_version()
    else:
        git_version = 'Unknown'

    full_version = prefs['version']
    if not preferences['released']:
        full_version += '.dev-' + git_version[:7]

    print('writing version file at %s' % filename)

    a = open(filename, 'w')
    try:
        a.write(cnt % {
            'version': prefs['version'],
            'short_version': prefs['version'],
            'full_version': full_version,
            'git_revision': git_version,
            'isrelease': str(prefs['released'])
        })
    finally:
        a.close()


# +-----------------------------------------------------------------------------
# | CONSTRUCT PARAMETERS FOR setuptools
# +-----------------------------------------------------------------------------

def build_keyword_dictionary(prefs):
    keywords = {}

    for key in [
        'name', 'version', 'license', 'url', 'download_url', 'packages',
        'package_dir', 'platforms', 'description', 'install_requires',
        'long_description', 'package_data', 'include_package_data'
    ]:
        if key in prefs:
            keywords[key] = prefs[key]

    keywords['author'] = \
        ', '.join(prefs['authors'][:-1]) + ' and ' + \
        prefs['authors'][-1]

    keywords['author_email'] = \
        ', '.join(prefs['emails'])

    keywords["package_dir"] = \
        {package: '/'.join(package.split('.')) for package in prefs['packages']}

    keywords['long_description'] = \
        trunc_lines(keywords['long_description'])

    output = ""
    first_tab = 40
    second_tab = 60
    for key in sorted(keywords.keys()):
        value = keywords[key]
        output += key.rjust(first_tab) + str(value).rjust(second_tab) + ""

    # pprint.pprint(keywords)
    # print("%s" % output)

    return keywords


# load settings from setup.py, easier to maintain, but not fully supported yet
# with open('setup.yaml') as f:
#     yaml_string = ''.join(f.readlines())
#     preferences = yaml.load(yaml_string)

preferences = {
    'authors': [
        'David W.H. Swenson',
        'Jan-Hendrik Prinz',
        'John D. Chodera',
        'Peter Bolhuis'
    ],
    'classifiers':
        '''
Development Status :: 3 - Alpha
Intended Audience :: Science/Research
Intended Audience :: Developers
License :: OSI Approved :: GNU Lesser General
Public License v2.1 or later (LGPLv2.1+)
Programming Language :: C
Programming Language :: Python
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3.6
Topic :: Scientific/Engineering :: Bio-Informatics
Topic :: Scientific/Engineering :: Chemistry
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
''',
    'description': 'OpenPathSampling: A python package to do path sampling simulations',
    'download_url': 'http://github.com/openpathsampling/openpathsampling',
    'emails': [
        'dwhs@hyperblazer.net',
        'jan.prinz@choderalab.org,',
        'choderaj@mskcc.org',
        'p.g.bolhuis@uva.nl'],
    'license': 'LGPL 2.1 or later',
    'license_file': 'LICENSE',
    'long_description': 'OpenPathSampling (http://github.com/choderalab/openpathsampling) is a \n'
                        'python library to do transition interface sampling.',
    'name': 'openpathsampling',
    'include_package_data': True,
    'packages': [
        'openpathsampling',
        'openpathsampling.storage',
        'openpathsampling.storage.stores',
        'openpathsampling.tests',
        'openpathsampling.analysis',
        'openpathsampling.netcdfplus',
        'openpathsampling.high_level',
        'openpathsampling.pathsimulators',
        'openpathsampling.engines',
        'openpathsampling.engines.features',
        'openpathsampling.engines.openmm',
        'openpathsampling.engines.openmm.features',
        'openpathsampling.engines.toy',
        'openpathsampling.engines.toy.features',
        'openpathsampling.numerics'],
    'platforms': ['Linux', 'Mac OS X', 'Windows'],
    'released': False,
    'install_requires': [
        #'python',
        'numpy',
        'scipy',
        'pandas',
        'future',
        'jupyter',
        'netcdf4',
        'openmm',
        'openmmtools',
        # 'pymbar',
        # 'docopt',
        # 'pyyaml',
        'mdtraj',
        'svgwrite',
        'networkx',
        'matplotlib',
        'ujson'],
    'url': 'http://www.openpathsampling.org',
    'version': '0.9.6'}

setup_keywords = build_keyword_dictionary(preferences)


def main():
    write_version_py(preferences)
    setup(**setup_keywords)
    pass


if __name__ == '__main__':
    main()
