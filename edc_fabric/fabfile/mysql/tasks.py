import os

from datetime import datetime

from fabric.api import run, task, env, cd, put, sudo, warn
from fabric.contrib.files import exists, sed

from ..constants import MACOSX, LINUX
from fabric.context_managers import prefix
from fabric.colors import yellow


def install_protocol_database(db_archive_name=None, dbname=None,
                              dbuser=None, dbpasswd=None, skip_backup=None,
                              release=None, map_area=None):
    if not skip_backup:
        backup_database(dbname=dbname, dbuser=dbuser, dbpasswd=dbpasswd)
    drop_database(dbname=dbname, dbuser=dbuser, dbpasswd=dbpasswd)
    create_database(dbname=dbname, dbuser=dbuser, dbpasswd=dbpasswd)
    restore_database(
        db_archive_name=db_archive_name,
        dbname=dbname, dbuser=dbuser,
        release=release, map_area=map_area)


def create_database(dbname=None, dbuser=None, dbpasswd=None):
    dbname = dbname or env.dbname
    dbuser = dbuser or env.dbuser
    dbpasswd = dbpasswd or env.dbpasswd
    run("mysql -u{dbuser} -p{dbpasswd} -Bse 'create database {dbname} character set utf8;'".format(
        dbuser=dbuser, dbname=dbname, dbpasswd=dbpasswd))


def backup_database(dbname=None, dbuser=None, dbpasswd=None):
    dbname = dbname or env.dbname
    dbuser = dbuser or env.dbuser
    dbpasswd = dbpasswd or env.dbpasswd
    if not exists('~/db_archives'):
        run('mkdir ~/db_archives')
    archive_filename = '{dbname}_{timestamp}.sql'.format(
        dbname=dbname, timestamp=datetime.now().strftime('%Y%M%d%H%M%S'))
    archive_path = os.path.join('~/db_archives', archive_filename)
    run('mysqldump {dbname} -u{dbuser} -p{dbpasswd} -r {archive_path}'.format(
        dbname=dbname, dbuser=dbuser, dbpasswd=dbpasswd, archive_path=archive_path), warn_only=True)


def drop_database(dbname=None, dbuser=None, dbpasswd=None):
    dbname = dbname or env.dbname
    dbuser = dbuser or env.dbuser
    dbpasswd = dbpasswd or env.dbpasswd
    run("mysql -u{dbuser} -p{dbpasswd} -Bse 'drop database {dbname};'".format(
        dbuser=dbuser, dbname=dbname, dbpasswd=dbpasswd), warn_only=True)


def restore_database(db_archive_name=None, dbname=None, dbuser=None,
                     dbpasswd=None, release=None, map_area=None):
    """Restores DB from db_archive_name in deployment database dir.
    """
    dbname = dbname or env.dbname
    dbuser = dbuser or env.dbuser
    dbpasswd = dbpasswd or env.dbpasswd
    release = release or env.project_release
    map_area = map_area or env.map_area
    with cd(os.path.join(env.deployment_database_dir, release, map_area)):
        db_archive_name = run('ls')
        # print('db_archive_name', db_archive_name)
        run("mysql -u{dbuser} -p{dbpasswd} {dbname} < {db_archive_name}".format(
            dbuser=dbuser, dbname=dbname, dbpasswd=dbpasswd,
            db_archive_name=db_archive_name))


def install_mysql():
    if env.target_os == MACOSX:
        install_mysql_macosx()
    elif env.target_os == LINUX:
        install_mysql_linux()


def install_mysql_macosx():
    env.prompts.update({'Enter password for user root: ': env.dbpasswd})
    result = run('mysql -V', warn_only=True)
    if 'Ver 14.14 Distrib 5.7.17' not in result:
        with prefix('export HOMEBREW_NO_AUTO_UPDATE=1'):
            run('brew tap homebrew/services')
            result = run('brew install mysql', warn_only=True)
            if 'Error' in result:
                run('brew unlink mysql')
                run('brew install mysql')
            run('brew services start mysql')
            run('brew switch mysql 5.7.17')
            run('mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root mysql', warn_only=True)
            if not env.dbpasswd:
                warn('{host}: DB password not set'.format(host=env.host))
                run('mysql_secure_installation')
            result = run('mysql -V')
    put_mysql_conf()
    with prefix('export HOMEBREW_NO_AUTO_UPDATE=1'):
        run('brew services stop mysql', quiet=True)
        run('brew services start mysql', warn_only=True)


def put_mysql_conf():
    if not exists(env.etc_dir):
        sudo('mkdir -p {etc_dir}'.format(etc_dir=env.etc_dir))
    old_path = os.path.join(env.etc_dir, 'my.cnf')
    if exists(old_path):
        sudo(f'rm {old_path}')
    mysql_conf = os.path.join(env.etc_dir, 'mysql.conf')
    put(os.path.expanduser(os.path.join(env.fabric_config_root, 'conf', 'mysql', 'mysql.conf')),
        mysql_conf, use_sudo=True)
    sed(mysql_conf, 'database \=.*',
        'database \= {dbname}'.format(dbname=env.dbname),
        use_sudo=True)
    sed(mysql_conf, 'password \=.*',
        'password \= {dbpasswd}'.format(dbpasswd=env.dbpasswd),
        use_sudo=True)


def put_my_cnf():
    my_cnf = '~/.my.cnf'
    put(os.path.expanduser(os.path.join(env.fabric_config_root, 'conf', 'mysql', 'my.cnf')),
        my_cnf)


def install_mysql_linux():
    sudo('sudo apt-get install mysql-server libmysqlclient-dev')
    run('mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root mysql', warn_only=True)
    sudo('mysql_secure_installation')
    sudo('service mysql stop', warn_only=True)
    sudo('service mysql start')
    # run('service status mysql.service')
    result = run(f'mysqladmin -uroot -p{env.dbpasswd} version', warn_only=True)
    if env.mysql_version not in result:
        warn(yellow(f'{env.host}: result'))


@task
def uninstall_mysql_macosx():
    run('brew services stop mysql', warn_only=True)
    run('brew remove mysql', warn_only=True)
    run('brew cleanup', warn_only=True)
    sudo('rm /usr/local/mysql', warn_only=True)
    sudo('rm -rf /usr/local/var/mysql', warn_only=True)
    sudo('rm -rf /usr/local/mysql*', warn_only=True)
    sudo('rm ~/Library/LaunchAgents/homebrew.mxcl.mysql.plist', warn_only=True)
    sudo('rm -rf /Library/StartupItems/MySQLCOM', warn_only=True)
    sudo('rm -rf /Library/PreferencePanes/My*', warn_only=True)
    run('launchctl unload -w ~/Library/LaunchAgents/homebrew.mxcl.mysql.plist', warn_only=True)
    # edit /etc/hostconfig and remove the line MYSQLCOM=-YES-
    run('rm -rf ~/Library/PreferencePanes/My*', warn_only=True)
    sudo('rm -rf /Library/Receipts/mysql*', warn_only=True)
    sudo('rm -rf /Library/Receipts/MySQL*', warn_only=True)
    sudo('rm -rf /private/var/db/receipts/*mysql*', warn_only=True)
