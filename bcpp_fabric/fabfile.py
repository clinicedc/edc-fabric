from __future__ import with_statement
from fabric.api import local
from unipath import Path
import os

from fabric.api import *
from fabric.utils import error, warn
# from fabric.contrib.files import exists
from fabric.colors import green, blue
from fabric.contrib.console import confirm

from hosts import HOSTS

BASE_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
NGINX_DIR = os.path.join(BASE_DIR.ancestor(1), 'nginx_deployment')
GUNICORN_DIR = NGINX_DIR
hosts = HOSTS

env.hosts = [host for host in hosts.keys()]
env.passwords = hosts
env.usergroup = 'django'
env.account = 'django'

env.virtualenv_name = 'bcpp'
env.source_dir = '/Users/django/source'
PROJECT_DIR = os.path.join(env.source_dir, 'bcpp')

env.update_repo = False

if env.update_repo is None:
    raise ("env.update_repo cannot be None, Set env.update_repo = True for update. Set env.update_repo = False for initial deployment.")

env.create_db = False
env.drop_and_create_db = True

env.custom_config_is = False


@task
def custom_config():
    if confirm('Do you want to customize deployment y/n'.format('bcpp'),
               default=True):
        env.custom_config_is = True


class FabricException(Exception):
    pass


@task
def remove_virtualenv():
    def _setup():
        result = run('rmvirtualenv {}'.format(env.virtualenv_name))
        if result.succeeded:
            print(blue('removing {} virtualenv .....'.format(env.virtualenv_name)))
            print(green('{} virtualenv removed.'.format(env.virtualenv_name)))
        else:
            error(result)
    if env.custom_config_is:
        if confirm('Do you want to remove virtual enviroment {} y/n?'.format('bcpp'),
                   default=True):
            _setup()
    else:
        _setup()


@task
def create_virtualenv():
    def _setup():
        print(blue('creating {} virtualenv .....'.format(env.virtualenv_name)))
        run('mkvirtualenv -p python3 {}'.format(env.virtualenv_name))
        print(green('{} virtualenv created.'.format(env.virtualenv_name)))

    if env.custom_config_is:
        if confirm('Do you want to create virtual environment {} y/n?'.format('bcpp'),
                   default=True):
            _setup()
    else:
        _setup()


@task
def clone_bcpp():
    def _setup():
        run('mkdir -p {}'.format(env.source_dir))
        with cd(env.source_dir):
            run('git clone https://github.com/botswana-harvard/bcpp.git')

    if env.custom_config_is:
        if confirm('Do you want to clone {} y/n?'.format('bcpp'),
                   default=True):
            _setup()
    else:
        _setup()


@task
def install_requirements():
    def _setup():
        with cd(PROJECT_DIR):
            with prefix('workon bcpp'):
                run('pip install -r requirements.txt -U')
    if env.custom_config_is:
        if confirm('Do you want to install the {} requirements y/n?'.format('bcpp'),
                   default=True):
            _setup()
    else:
        _setup()


@task
def create_db_or_dropN_create_db():
    if env.drop_and_create_db:
        if confirm('Are you sure you want create a new {} database  y/n'.format('edc'),
                   default=False):
            with settings(abort_exception=FabricException):
                try:
                    run("mysql -uroot -p -Bse 'drop database edc; create database edc character set utf8;'")
                    print(green('edc database has been created.'))
                except FabricException:
                    run("mysql -uroot -p -Bse 'create database edc character set utf8;'")


@task
def fake_migrations():
    def _setup():
        run(managepy, 'migrate --fake')

    if env.custom_config_is:
        if confirm('Do you want to run fake migrations y/n?'.format('bcpp'),
                   default=True):
            _setup()
    else:
        _setup()


@task
def migrate():
    def _setup():
        with prefix('workon bcpp'):
            with cd(PROJECT_DIR):
                run('python manage.py makemigrations plot household member bcpp_subject')
                run('python manage.py makemigrations')
                run('python manage.py migrate')

    if env.custom_config_is:
        if confirm('Do you want to run migrations y/n?'.format('bcpp'),
                   default=True):
            _setup()
    else:
        _setup()


@task
def make_keys_dir():
    with cd(PROJECT_DIR):
        run('mkdir  -p crypto_fields')
        run('mkdir  -p media/edc_map')


@task
def collectstatic():
    with cd(PROJECT_DIR):
        with prefix('workon bcpp'):
            run('python manage.py collectstatic')


@task
def check_hostnames():
    last_bit = ''
    for digit in hostname()[0]:
        if digit.isdigit():
            last_bit += str(digit)
    try:
        id = int(last_bit)
        if id < 10:
            id += 80
            print(green("The device id: {}".format(id)))
            return id
        return id
    except ValueError:
        raise ValueError('{0} is not an expected hostname'.format(hostname()[0]))


def hostname():
    hostname = sudo('hostname')
    return (hostname, env.host,)


@task
def tranfer_db():
    pass


@task
def create_db_dump():
    with cd('/Users/django/Desktop/'):
        run('mysqldump -uroot -pcc3721b edc -r file.sql')


@task
def restore_db():
    with cd('/Users/django/Desktop/'):
        run('tar -xvzf bhp066_master_201601191025.sql.tar.gz')
        run("mysql -uroot -pcc3721b -Bse 'drop database bhp066; create database bhp066;SET GLOBAL max_allowed_packet=1073741824;'")
        run("mysql -uroot -pcc3721b bhp066 < bhp066_master_201601191025.sql")


@task
def initial_setup():
    execute(check_hostnames)
    execute(remove_virtualenv)
    execute(create_virtualenv)
    execute(clone_bcpp)
    execute(install_requirements)
    execute(create_db_or_dropN_create_db)
    execute(make_keys_dir)
    execute(mysql_tzinfo)
    execute(migrate)
    execute(collectstatic)
#     execute(load_fixtures)
    execute(setup_nginx)
    execute(setup_gunicorn)
    execute(stopNstart_nginx_and_gunicorn)


@task
def setup_gunicorn():
    with prefix('workon bcpp'):
        run('pip install gunicorn')
    put(os.path.join(GUNICORN_DIR, 'gunicorn.conf.py'), PROJECT_DIR, use_sudo=True)
    with cd(PROJECT_DIR):
        run('mkdir -p logs')
        chmod('755', os.path.join(PROJECT_DIR, 'logs'), dirr=True)
        with cd(os.path.join(PROJECT_DIR, 'logs')):
                run('touch gunicorn-access.log')
                run('touch gunicorn-error.log')
    print(green('gunicorn setup completed.'))


@task
def setup_nginx():
    def _setup():
        sudo("mkdir -p /usr/local/etc/nginx/sites-available")
        sudo("mkdir -p /usr/local/etc/nginx/sites-enabled")
        chmod('755', '/usr/local/etc/nginx/sites-available', dirr=True)
        put(os.path.join(NGINX_DIR, 'nginx.conf'),
            '/usr/local/etc/nginx/nginx.conf', use_sudo=True)
        put(os.path.join(NGINX_DIR, 'bcpp.conf'),
            '/usr/local/etc/nginx/sites-available/bcpp.conf', use_sudo=True)
        with cd('/usr/local/etc/nginx/sites-enabled'):
            try:
                sudo('ln -s /usr/local/etc/nginx/sites-available/bcpp.conf bcpp.conf')
            except:
                print(blue('nginx symbolic already created.'))
        print(green('nginx setup completed.'))

    if env.custom_config_is:
        if confirm('Do you want to setup nginx y/n?'.format('bcpp'),
                   default=True):
            _setup()
    else:
        _setup()


def stop_nginxN_gunicorn():
    try:
        sudo('nginx -s stop')
        sudo('pgrep gunicorn | xargs kill -9')
    except:
        pass


@task
def stopNstart_nginx_and_gunicorn():
    def _setup():
        stop_nginxN_gunicorn()
        sudo('nginx')
        with cd(PROJECT_DIR):
            with prefix('workon bcpp'):
                run('gunicorn -c gunicorn.conf.py bcpp.wsgi --pid /Users/django/source/bcpp/logs/gunicorn.pid --daemon')
        print(green('nginx & gunicorn restarted.'))

    if env.custom_config_is:
        if confirm('Do you want to stop and start nginx y/n?'.format('bcpp'),
                   default=True):
            _setup()
    else:
        _setup()


@task
def update_project():
    def _setup():
        with prefix('workon bcpp'):
            with cd(PROJECT_DIR):
                run('git pull')
                run('pip install -r requirements.txt -U')

    if env.custom_config_is:
        if confirm('Do you want to stop and start nginx y/n?'.format('bcpp'),
                   default=True):
            _setup()
    else:
        _setup()


@task
def deploy():
    with settings(abort_exception=FabricException):
        execute(custom_config)
        try:
            if not env.update_repo:
                execute(initial_setup)
            else:
                execute(update_project)
        except FabricException as e:
            print(e)

@task
def mysql_tzinfo():
    run('mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql')


@task
def load_fixtures():
    with cd(PROJECT_DIR):
        with prefix('workon bcpp'):
            run(' python  manage.py load_fixtures')


@task
def managepy(command=None):
    with cd(PROJECT_DIR):
        with prefix('workon bcpp'):
            sudo('./manage.py {command}'.format(command=command))


def chmod(permission, file, dirr=False):
    if dirr:
        sudo("chmod -R %s %s" % (permission, file))
    else:
        sudo("chmod %s %s" % (permission, file))


def chown(name, dirr=True):
    if dirr:
        sudo('chown -R {account}:staff {filename}'.format(account=env.account, filename=name))
    else:
        sudo('chown {account}:staff {filename}'.format(account=env.account, filename=name))
