from __future__ import with_statement
from fabric.api import local
from unipath import Path
import os

from fabric.api import *
from fabric.utils import error, warn
from fabric.contrib.files import exists
from fabric.colors import green, red, blue
from fabric.contrib.console import confirm
from .hosts import HOSTS

hosts = HOSTS

BASE_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
NGINX_DIR = os.path.join(BASE_DIR.ancestor(1), 'nginx_deployment')
GUNICORN_DIR = NGINX_DIR

env.hosts = [host for host in hosts.keys()]
env.passwords = hosts

env.virtualenv_name = 'bcpp'
env.source_dir = '/Users/django/source'
PROJECT_DIR = os.path.join(env.source_dir, 'bcpp')

env.update_repo = False

env.create_db = False
env.drop_and_create_db = True


class FabricException(Exception):
    pass

@task
def remove_virtualenv():
    result = run('rmvirtualenv {}'.format(env.virtualenv_name))
    if result.succeeded:
        print(blue('removing {} virtualenv .....'.format(env.virtualenv_name)))
        print(green('{} virtualenv removed.'.format(env.virtualenv_name)))
    else:
        error(result)

@task
def create_virtualenv():
    print(blue('creating {} virtualenv .....'.format(env.virtualenv_name)))
    run('mkvirtualenv -p python3 {} --no-site-packages'.format(env.virtualenv_name))
    print(green('{} virtualenv created.'.format(env.virtualenv_name)))

@task
def clone_bcpp():
    run('mkdir -p {}'.format(env.source_dir))
    with cd(env.source_dir):
        run('git clone https://github.com/botswana-harvard/bcpp.git')

@task
def install_requirements():
    with cd(PROJECT_DIR):
        with prefix('workon bcpp'):
            run('pip install -r requirements.txt -U')

@task
def create_db_or_dropN_create_db():
    if env.drop_and_create_db:
        if confirm('Are you sure you want to drop database {} and create it? y/n'.format('bcpp'),
                               default=False):
            with settings(abort_exception=FabricException):
                try:
                    run("mysql -uroot -p -Bse 'drop database edc; create database edc character set utf8;'")
                except FabricException:
                    run("mysql -uroot -p -Bse 'create database edc character set utf8;'")

@task
def migrate():
    with prefix('workon bcpp'):
        with cd(PROJECT_DIR):
            run('python manage.py makemigrations plot household member bcpp_subject')
            run('python manage.py makemigrations')
            run('python manage.py migrate')

@task
def make_keys_dir():
    with cd(PROJECT_DIR):
        run('mkdir  -p crypto_fields')
        run('mkdir  -p media/edc_map')

@task
def initial_setup():
    execute(remove_virtualenv)
    execute(create_virtualenv)
    execute(clone_bcpp)
    execute(install_requirements)
    execute(create_db_or_dropN_create_db)
    execute(make_keys_dir)
    execute(migrate)
    manage_py('collectstatic --noinput')
    execute(setup_nginx)
    execute(setup_gunicorn)
    execute(stopNstart_nginx_and_gunicorn)

@task
def setup_gunicorn():
    with prefix('workon bcpp'):
        run('pip install gunicorn')
    put(os.path.join(GUNICORN_DIR, 'gunicorn.conf'), PROJECT_DIR)
    with cd(PROJECT_DIR):
        run('mkdir -p logs')
        with cd(os.path.join(PROJECT_DIR, 'logs')):
                run('touch gunicorn-access.log')
                run('touch gunicorn-error.log')

@task
def setup_nginx():
    sudo("mkdir -p /usr/local/etc/nginx/sites-available")
    put(os.path.join(NGINX_DIR, 'bcpp.conf'), '/usr/local/etc/nginx/sites-available/bcpp.conf')
    with cd('/usr/local/etc/nginx/sites-enabled'):
        sudo('ln -s /usr/local/etc/nginx/sites-available/bcpp.conf bcpp.conf')

@task
def stopNstart_nginx_and_gunicorn():
    sudo('nginx -s stop')
    sudo('nginx')
    sudo('pkill gunicorn')
    with cd(PROJECT_DIR):
        with prefix('workon bcpp'):
            run('gunicorn -c gunicorn.conf.py bcpp.wsgi --pid /Users/django/source/bcpp/logs/gunicorn.pid --daemon')
    print(green('nginx & gunicorn restarted.'))

@task
def update_project():
    with prefix('workon bcpp'):
        with cd(PROJECT_DIR):
            run('git pull')
            run('pip install -r requirements.txt -U')

@task
def deploy(server=None):
    with settings(abort_exception=FabricException):
        try:
            if not env.update_repo:
                execute(initial_setup)
            else:
                execute(update_project)
        except FabricException as e:
            print(e)
