from fabric.api import task
from fabric.operations import local


@task
def runserver():
    local('python runserver.py')

@task
def runapp(appname):
    local('PYTHONPATH=. python example_apps/'+appname+'.py')

@task
def babel(command):
    # Generate the .pot file from source code files
    if command=='extract':
        local('pybabel extract -F flask_auth/translations/babel.cfg -k lazy_gettext -c NOTE -o flask_auth/translations/flask_auth.pot flask_auth flask_auth')

    # Update .po files from the .pot file
    elif command=='update':
        local('pybabel update -i flask_auth/translations/flask_auth.pot --domain=flask_auth --output-dir flask_auth/translations')
    elif command=='compile':
        local('pybabel compile -f --domain=flask_auth --directory flask_auth/translations')

@task
def test():
    # Requires "pip install pytest"
    local('py.test flask_auth/tests/')

@task
def cov():
    # Requires "pip install pytest-coverage"
    local('py.test --cov flask_auth --cov-report term-missing --cov-config flask_auth/tests/.coveragerc flask_auth/tests/')

@task
def cov2():
    # Requires "pip install pytest-coverage"
    local('py.test --cov flask_auth --cov-report term-missing --cov-config flask_auth/tests/.coveragerc flask_auth/tests/test_views.py')

@task
def profiling():
    # Requires "pip install pytest-profiling"
    local('py.test --profile flask_auth/tests/')


@task
def docs(rebuild=False):
    # local('cp example_apps/*_app.py docs/source/includes/.')
    options=''
    if rebuild:
        options += ' -E'
    local('sphinx-build -b html -a {options} docs/source ../builds/flask_auth1/docs'.format(options=options))
    local('cd ../builds/flask_auth1/docs && zip -u -r flask_auth1_docs *')

# sphinx-apidoc -f -o docs/source flask_auth flask_auth/tests flask_auth/db_adapters
# rm docs/source/flask_auth.rst docs/source/modules.rst

# PyEnv: https://gist.github.com/Bouke/11261620
# PyEnv and Tox: https://www.holger-peters.de/using-pyenv-and-tox.html
# Available Python versions: pyenv install --list
@task
def setup_tox():
    versions_str = '2.6.9 2.7.13 3.3.6 3.4.6 3.5.3 3.6.2'
    versions = versions_str.split()
    for version in versions:
        local('pyenv install --skip-existing '+version)
    local('pyenv global '+versions_str)

@task
def tox():
    local('tox')

@task
def start_mongodb():
    local('mongod -dbpath ~/mongodb/data/db')

@task
def build_dist():
    # Compile translation files
    babel('compile')
    # Build distribution file
    local('rm -f dist/*')
    local('python setup.py sdist')

@task
def upload_to_pypi():
    build_dist()
    local('twine upload dist/*')

