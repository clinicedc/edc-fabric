from __future__ import with_statement
from fabric.api import local
from unipath import Path
import os

from fabric.api import *
from fabric.utils import error, warn
# from fabric.contrib.files import exists
from fabric.colors import green, blue, red
from fabric.contrib.console import confirm

from hosts import HOSTS
from repo_list import REPOS
from databases import DATABASES, DATABASE_FILES
from fabric.decorators import parallel

BASE_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
NGINX_DIR = os.path.join(BASE_DIR.ancestor(1), 'nginx_deployment')
GUNICORN_DIR = NGINX_DIR
hosts = HOSTS
database_files = DATABASE_FILES
env.old_code = 12
env.new_code = 30
env.repos = REPOS
env.hosts = [host for host in hosts.keys()]
env.database_files = [database_files for database_files in database_files.keys()]
env.passwords = hosts
env.database_file = env.database_files[0]
env.compressed_db_name = '{}.tar.gz'.format(env.database_file)
env.usergroup = 'django'
env.account = 'django'
env.mysql_root_passwd = 'cc3721b'
env.server = '10.113.200.222'
env.local_path = os.path.join(BASE_DIR, env.database_file)

env.server_ssh_key_location = 'django@10.113.201.134:~/'

a_dir = a_file = "{0}/{1}".format

FAB_DIR = 'fabric'
env.keys = 'crypto_fields'

env.repos = 'all_repos'
env.repo_local_path = os.path.join(BASE_DIR, 'all_repos.tar.gz')
env.repo_unpacked = os.path.join(BASE_DIR)
FAB_SQL_DIR = a_dir(FAB_DIR, 'sql')

env.virtualenv_name = 'bcpp'
env.database_folder = '/Users/django/databases/community'
env.source_dir = '/Users/django/source'
PROJECT_DIR = os.path.join(env.source_dir, 'bcpp')
env.python_dir = '/usr/bin'
env.update_repo = False

SETTINGS_DIR = a_dir(PROJECT_DIR, 'bcpp')
CONFIG_DIR = a_dir(SETTINGS_DIR, 'config')
SETTINGS_FILE = a_file(SETTINGS_DIR, 'settings.py')

if env.update_repo is None:
    raise ("env.update_repo cannot be None, Set env.update_repo = True for update."
           ("Set env.update_repo = False for initial deployment."))

env.create_db = False
env.drop_and_create_db = True

env.custom_config_is = False

env.new_community = 'test_community'
env.old_community = 'digawana'


@task
def print_test():
    run('mkdir -p {}'.format(env.database_folder))
#     print(env.repo_unpacked)
#     print(env.local_path)
#     print(env.host)


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
        result = sudo('rmvirtualenv {}'.format(env.virtualenv_name))
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
        print(blue('creating {} virtualenv > '.format(env.virtualenv_name)))
        run('mkvirtualenv -p python3 {}'.format(env.virtualenv_name))
        print(green('{} virtualenv created.'.format(env.virtualenv_name)))

    if env.custom_config_is:
        if confirm('Do you want to create virtual environment {} y/n?'.format(env.virtualenv_name),
                   default=True):
            _setup()
    else:
        _setup()


@task
def clone_bcpp():
    def _setup():
        sudo('rm -rf {}'.format(PROJECT_DIR))
        run('mkdir -p {}'.format(env.source_dir))
        with cd(env.source_dir):
            run('git clone -b master https://github.com/botswana-harvard/bcpp.git')

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
                run('pip install -r requirements.txt -U ')
    if env.custom_config_is:
        if confirm('Do you want to install the {} requirements y/n?'.format('bcpp'),
                   default=True):
            _setup()
    else:
        _setup()


@task
def create_db_or_dropN_create_db():
    if env.drop_and_create_db:
        try:
            run("mysql -uroot -p%s -Bse 'drop database edc; create database edc character set utf8;'" % (env.mysql_root_passwd))
            run("mysql -uroot -p%s -Bse 'alter table mysql.time_zone_transition_type modify Abbreviation CHAR(50);'" % (env.mysql_root_passwd))
            print(green('edc database has been created.'))
        except FabricException:
                    run("mysql -uroot -p%s -Bse 'create database edc character set utf8;'" % (env.mysql_root_passwd))


@task
def compress_db():
    with cd(BASE_DIR):
        local('tar -czvf {} {}'.format(env.compressed_db_name, env.database_file))


@task
def restore_database():
    execute(create_db_or_dropN_create_db)
    execute(transfer_db)
    with cd(env.database_folder):
        execute_sql_file(env.database_file)


def execute_sql_file(sql_file):
    try:
        run('mysql -uroot -p%s edc < %s' % (env.mysql_root_passwd, sql_file))
    except FabricException as e:
        print(red('Failed to restore database {} Got {}'.format(sql_file, e)))


@task
def transfer_db():
    run('mkdir -p {}'.format(env.database_folder))
    try:
        with cd(PROJECT_DIR):
            put(env.local_path, '{}/{}'.format(env.database_folder, env.database_file))
            print(green('Database file sent.'))
    except FabricException as e:
        print(red('file tranfer failed {}'.format(e)))


@task
def transfer_db_compressed():
    run('mkdir -p {}'.format(env.database_folder))
    try:
        with cd(env.source_dir):
            #execute(compress_db)
            put(os.path.join(BASE_DIR, env.compressed_db_name), '{}/{}'.format(env.database_folder, env.compressed_db_name))
            print(green('Database file sent.'))
    except FabricException as e:
        print(red('file tranfer failed {}'.format(e)))


@task
def restore_database_compressed():
    execute(create_db_or_dropN_create_db)
    execute(transfer_db_compressed)
    with cd(env.database_folder):
        run('tar -xvzf {}'.format(env.compressed_db_name))
        execute_sql_file(env.database_file)


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
        run('mkdir -p crypto_fields')
        run('mkdir  -p media/edc_map')
    with cd(PROJECT_DIR):
        run('scp -r django@bcpp3:~/edc_migrated/crypto_keys.dmg .')
        run('hdiutil attach -stdinpass crypto_keys.dmg')


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


def hostname():
    hostname = sudo('hostname')
    return (hostname, env.host,)


@task
def get_device_id():
    last_bit = ''
    for digit in hostname()[0]:
        if digit.isdigit():
            last_bit += str(digit)

    device_id = int(last_bit)
    try:
        if device_id < 10:
            device_id += 80
        return device_id
    except ValueError:
        raise ValueError('{0} is not an expected hostname'.format(hostname()[0]))


@task
def set_device_id():
    with cd(PROJECT_DIR):
        try:
            device_id = get_device_id()
            replace_device_id = sudo("sed -i.bak 's/DEVICE_ID = .*/DEVICE_ID = {}/g' {}" .format(device_id, SETTINGS_FILE))
            if replace_device_id.succeeded:
                print(blue('Replaced device id'))
            chmod('755', SETTINGS_FILE)
            chown(SETTINGS_FILE, dirr=False)

        except:
            pass


@task
def install_dependencies():
    with prefix('workon bcpp'):
        run('pip install ipython')
        run('pip install Fabric3')
        run('pip install Unipath')
        run('pip install Django')
        run('pip install django-crispy-forms')
        run('pip install django-tz-detect')
        run('pip install -b master git+https://github.com/erikvw/django-crypto-fields.git')
        run('pip install -b master git+https://github.com/erikvw/django-revision.git')


@task
def get_device_id_value():
    result = run('grep -i "DEVICE_ID = * " {}'.format(SETTINGS_FILE))
    if result.succeeded:
        print('Found >>>')
    else:
        print('not found <<<')


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
                run('git checkout master')
                run('git pull')
        with cd(env.source_dir):
            for repo in REPOS:
                with cd(repo):
                    run('pwd')
                    print('Updating {}'.format(repo))
                    run('git pull')

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
            startlog()
            execute(checkdeployment)


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
    with PROJECT_DIR:
        run('touch {}.log'.format(env.hosts[0]))
        file = ('{}.log'.format(env.hosts[0]))
        logfile = open(file, "a+")
        run(execute(clone_bcpp))
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
        run('ssh-keygen -t rsa -N ""')
        run('ssh-copy-id django@{}'.format(env.server))
    else:
        run('ssh-keygen -t rsa -N ""')
        run('brew install ssh-copy-id')
        result = run('which ssh-copy-id')
        if not result.failed:
            run('ssh-copy-id django@{}'.format(env.server))


@task
def modify_settings(replacements):
    "replacement should be a list of tuples"
#     get(SETTINGS_FILE, 'settings.py')
    with open(SETTINGS_FILE, 'rt') as old_settings:
        content = old_settings.read()
        for pair in replacements:
            content = content.replace(pair[0], pair[1])
        with open(SETTINGS_FILE, 'wt') as settings:
            settings.write(content)
#     put('settings.py', SETTINGS_FILE, use_sudo=False)
#     os.remove('settings.py')
    with cd(PROJECT_DIR):
        chmod('755', 'settings.py')


@task
def set_debug_false():
    with cd(PROJECT_DIR):
        replace_debug = sudo("sed -i.bak s'/DEBUG = True/DEBUG = False/' {}" .format(SETTINGS_FILE))
        if replace_debug.succeeded:
            print('File ran in debug false mode >>>')
        else:
            pass


@task
def set_debug_true():
    with cd(PROJECT_DIR):
        replace_debug = sudo("sed -i.bak s'/DEBUG = False/DEBUG = True/' {}" .format(SETTINGS_FILE))
        if replace_debug.succeeded:
            print('File ran in debug True mode >>>')
        else:
            pass


@task
def get_debug_value():
    result = run('grep -i "DEBUG = * " {}'.format(SETTINGS_FILE))
    if result.succeeded:
        print('Found >>>')
    else:
        print('not found <<<')


@task
def set_community(new_community=env.new_community):
    with cd(PROJECT_DIR):
        try:
            change_community = sudo("""sed -i.bak "s/CURRENT_MAP_AREA = .*/CURRENT_MAP_AREA = '{}'/g" {}""" .format(str(new_community), SETTINGS_FILE))
            if change_community.succeeded:
                print(blue('Replaced community'))
            chmod('755', SETTINGS_FILE)
            chown(SETTINGS_FILE, dirr=False)

        except:
            pass


@task
def clone_packages():
    local('mkdir -p all_repos')
    with cd('all_repos'):
        repo_dir = os.path.join(BASE_DIR, 'all_repos')
        for repo in REPOS:
            try:
                local('cd {}; git clone -b master https://github.com/botswana-harvard/{}.git'.format(repo_dir, repo))
            except:
                pass  # TODO ask to Update or Not
        local('tar -czvf all_repos.tar.gz -C {} .'.format(repo_dir))


@task
def install_local_repos():
    execute(clone_bcpp)
    with cd(env.source_dir):
        sudo('rm -rf all_packages')
        run('mkdir -p all_packages')
        put(env.repo_local_path, 'all_packages')
        with cd('all_packages'):
            run('tar -xvzf all_repos.tar.gz')
            run('rm -rf all_repos.tar.gz')
    run('rsync -vau --delete-after {} {}'.format('/Users/django/source/all_packages/*', env.source_dir + "/"))
    run('rm -rf /Users/django/source/all_packages')
    execute(install_packages)


@task
def install_packages():
    with prefix('workon bcpp'):
        with cd(env.source_dir):
            for repo in REPOS:
                run('pip install -e ./{}/'.format(repo))


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


@task
def initial_setup():
    execute(set_device_id)
    execute(disable_apache_on_startup)
    execute(remove_virtualenv)
    execute(make_keys_dir)
    execute(create_virtualenv)
    execute(install_dependencies)
    execute(install_local_repos)
    execute(make_keys_dir)
    execute(set_debug_false)
#     execute(setup_ssh_key_pair)
    execute(create_db_or_dropN_create_db)
    execute(mysql_tzinfo)
#     execute(restore_database)
#     execute(fake_migrations)
#     execute(migrate)
    execute(setup_nginx)
    execute(setup_gunicorn)
#     execute(load_fixtures)
    execute(collectstatic)
    execute(staticjs_reverse)
    execute(start_webserver)
