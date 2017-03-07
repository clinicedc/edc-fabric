from __future__ import with_statement
from fabric.api import local
from unipath import Path
import os

from fabric.api import *
from fabric.utils import error, warn
# from fabric.contrib.files import exists
from fabric.colors import green, blue, red
from fabric.contrib.console import confirm

from hosts import HOSTS, CLIENTS
from databases import DATABASES, DATABASE_FILES

BASE_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
NGINX_DIR = os.path.join(BASE_DIR.ancestor(1), 'nginx_deployment')
GUNICORN_DIR = NGINX_DIR
hosts = HOSTS
clients = CLIENTS
database_files = DATABASE_FILES

env.hosts = [host for host in hosts.keys()]
env.clients = [clients for clients in clients.keys()]
env.database_files = [database_files for database_files in database_files.keys()]
env.passwords = hosts
env.database_file = env.database_files[0]
env.usergroup = 'django'
env.account = 'django'
env.mysql_root_passwd = 'cc3721b'
env.server = '10.113.200.166'
env.local_path = '/Users/gnmagodi/source/bcpp-fabric/bcpp_fabric/{}'.format(env.database_file)

env.server_ssh_key_location = 'django@10.113.201.134:~/'

a_dir = a_file = "{0}/{1}".format

FAB_DIR = 'fabric'
env.keys = 'crypto_fields'

FAB_SQL_DIR = a_dir(FAB_DIR, 'sql')

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
def print_test():
    print(env.local_path)


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

        print(blue('Installing django....'))
        sudo('pip install django')
        print(green('Successfully installed django'))

    if env.custom_config_is:
        if confirm('Do you want to create virtual environment {} y/n?'.format(env.virtualenv_name),
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
                    run("mysql -uroot -p%s -Bse 'drop database edc; create database edc character set utf8;'" % (env.mysql_root_passwd))
                    print(green('edc database has been created.'))
                except FabricException:
                    run("mysql -uroot -p%s -Bse 'create database edc character set utf8;'" % (env.mysql_root_passwd))


@task
def dump_backup():
    with cd(env.source_dir):
        sudo('mysqldump -uroot -p edc -r %s' % (env.dbname))


@task
def restore_database():
    execute(create_db_or_dropN_create_db)
    execute(transfer_db)
    with cd(PROJECT_DIR):
        run('scp -r django@bcpp3:/home/django/training_keys/crypto_fields .')
    with cd(PROJECT_DIR):
        execute_sql_file(env.database_file)
    execute(start_webserver)


def execute_sql_file(sql_file):
    try:
        run('mysql -uroot -p%s edc < %s' % (env.mysql_root_passwd, sql_file))
    except FabricException as e:
        print(red('Failed to restore database {} Got {}'.format(sql_file, e)))


@task
def transfer_db():
    try:
        with cd(PROJECT_DIR):
            put(env.local_path, PROJECT_DIR)
            print(green('Database file sent.'))
    except FabricException as e:
        print(red('file tranfer failed {}'.format(e)))


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
def compress_keys():
    with cd(PROJECT_DIR):
        local('tar -czvf crypto_fields.tar.gz {}'.format(os.path.join(BASE_DIR, env.keys)))


@task
def tranfer_compressed_keys():
    with cd(env.source_dir):
        put(os.path.join(BASE_DIR, env.keys), os.path.join(PROJECT_DIR, env.keys), use_sudo=True)


@task
def uncompressed_keys():
    with cd(env.source_dir):
        run('tar xopf {}'.format(env.keys))


@task
def collectstatic():
    with cd(PROJECT_DIR):
        with prefix('workon bcpp'):
            run('python manage.py collectstatic')


@task
def staticjs_reverse():
    with cd(PROJECT_DIR):
        with prefix('workon bcpp'):
            run('python manage.py collectstatic_js_reverse')


@task
def load_fixtures():
    with cd(PROJECT_DIR):
        with prefix('workon bcpp'):
            run('python manage.py load_fixtures')


@task
def check_hostnames():
    last_bit = ''
    for digit in hostname()[0]:
        if digit.isdigit():
            last_bit += str(digit)
    try:
        host_id = int(last_bit)
        if host_id < 10:
            host_id += 80
            print(green("The device id: {}".format(host_id)))
            return host_id
        return host_id
    except ValueError:
        raise ValueError('{0} is not an expected hostname'.format(hostname()[0]))


def hostname():
    hostname = sudo('hostname')
    return (hostname, env.host,)


@task
def initial_setup():
    execute(check_hostnames)
    execute(disable_apache_on_startup)
    execute(remove_virtualenv)
    execute(create_virtualenv)
    execute(clone_bcpp)
    execute(install_requirements)
    execute(create_db_or_dropN_create_db)
    execute(make_keys_dir)
#     execute(mysql_tzinfo)
    execute(restore_database)
#     execute(fake_migrations)
    execute(migrate)
    execute(collectstatic)
    execute(setup_nginx)
    execute(setup_gunicorn)
    execute(load_fixtures)
    execute(staticjs_reverse)
#     execute(start_webserver)


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


def stop_webserver():
    try:
        sudo('nginx -s stop')
        sudo('pgrep gunicorn | xargs kill -9')
    except:
        pass


@task
def start_webserver():
    def _setup():
        stop_webserver()
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
def deployment_activity_log_files():
    for host in hostname():
        with cd(PROJECT_DIR):
            file = run('touch {}.log'.format(host))
            put(file, PROJECT_DIR)


@task
def checkdeployment():
    with show('output', 'warnings', 'running'):
        try:
            startlog()
            log('task done')
        except Exception:
            print("%s host is down :: %s" % (env.hosts, str(Exception)))
            log('bad host %s::%s' % (env.hosts, str(Exception)))


def startlog():
    file = run('touch {}.log'.format(host))
    put(file, PROJECT_DIR)
    logfile = open(file, "a+")
    logfile.close()


def log(msg):
    logfile = open(startlog.file, "a+")
    logfile.write(msg + "\n")
    logfile.close()


@task
def disable_apache_on_startup():
    sudo('launchctl unload -w /System/Library/LaunchDaemons/org.apache.httpd.plist')


@task
def mysql_tzinfo():
    run('mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql')


@task
def setup_ssh_key_pair():
    result = run('which ssh-copy-id')
    if not result.failed:
        run('ssh-keygen')
        run('ssh-copy-id django@{}'.format(env.server))
    else:
        run('ssh-keygen')
        run('brew install ssh-copy-id')
        result = run('which ssh-copy-id')
        if not result.failed:
            run('ssh-copy-id django@{}'.format(env.server))


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
