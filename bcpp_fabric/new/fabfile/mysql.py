import os

from datetime import datetime
from fabric.api import run, task, env
from fabric.contrib.files import exists

from .constants import MACOSX, LINUX


@task
def create_database(dbname=None, root_user=None):
    root_user = root_user or 'root'
    run("mysql -u{root_user} -p -Bse 'create database {dbname} character set utf8;'".format(
        root_user=root_user, dbname=dbname))


@task
def backup_database(dbname=None, root_user=None):
    if not exists('~/db_archives'):
        run('mkdir ~/db_archives')
    archive_filename = '{dbname}_{timestamp}.sql'.format(
        dbname=dbname, timestamp=datetime.now().strftime('%Y%M%d%H%M%S'))
    archive_path = os.path.join('~/db_archives', archive_filename)
    run('mysqldump {dbname} -u root -p -r {archive_path}'.format(
        dbname=dbname, archive_path=archive_path))


@task
def drop_database(dbname=None, root_user=None, backup_first=None):
    backup_first = True if backup_first is None else backup_first
    if backup_first:
        backup_database(dbname=dbname, root_user=root_user)
    run("mysql -u{root_user} -p -Bse 'drop database {dbname};'".format(
        root_user=root_user, dbname=dbname))


def install_mysql(target_os=None):
    target_os = target_os or env.target_os
    if target_os == MACOSX:
        install_mysql_macosx()
    elif target_os == LINUX:
        install_mysql_linux()


@task
def install_mysql_macosx():
    result = run('mysql -V')
    print(result)
    if result != 'Ver 14.14 Distrib 5.7.15, for osx10.12 (x86_64)':
        run('brew services stop mysql', warn_only=True)
        run('brew install mysql')
        run('brew tap homebrew/services')
        run('brew services start mysql')
        run('mysqladmin -u root password \'{dbpassword}\''.format(env.dbpassword))
        result = run('mysql -V')


@task
def install_mysql_linux():
    pass
