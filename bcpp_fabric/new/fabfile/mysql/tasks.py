import os

from datetime import datetime

from fabric.api import run, task, env
from fabric.contrib.files import exists

from ..constants import MACOSX, LINUX


def install_protocol_database(db_archive_path=None, dbname=None,
                              dbuser=None, backup_first=None):
    backup_database(dbname=dbname, dbuser=dbuser)
    drop_database(dbname=dbname, dbuser=dbuser)
    restore_database(
        db_archive_path=db_archive_path,
        dbname=dbname, dbuser=dbuser)


def create_database(dbname=None, dbuser=None):
    dbname = dbname or env.dbname
    dbuser = dbuser or env.dbuser
    run("mysql -u{dbuser} -p -Bse 'create database {dbname} character set utf8;'".format(
        dbuser=dbuser, dbname=dbname))


def backup_database(dbname=None, dbuser=None):
    dbname = dbname or env.dbname
    dbuser = dbuser or env.dbuser
    if not exists('~/db_archives'):
        run('mkdir ~/db_archives')
    archive_filename = '{dbname}_{timestamp}.sql'.format(
        dbname=dbname, timestamp=datetime.now().strftime('%Y%M%d%H%M%S'))
    archive_path = os.path.join('~/db_archives', archive_filename)
    run('mysqldump {dbname} -u {dbuser} -p -r {archive_path}'.format(
        dbname=dbname, dbuser=dbuser, archive_path=archive_path))


def drop_database(dbname=None, dbuser=None):
    dbname = dbname or env.dbname
    dbuser = dbuser or env.dbuser
    run("mysql -u{dbuser} -p -Bse 'drop database {dbname};'".format(
        dbuser=dbuser, dbname=dbname))


def restore_database(db_archive_path=None, dbname=None, dbuser=None):
    dbname = dbname or env.dbname
    dbuser = dbuser or env.dbuser
    run("mysql -u{dbuser} -p {dbname} < {db_archive_path}".format(
        dbuser=dbuser, dbname=dbname, db_archive_path=db_archive_path))


def install_mysql():
    if env.target_os == MACOSX:
        install_mysql_macosx()
    elif env.target_os == LINUX:
        install_mysql_linux()


def install_mysql_macosx():
    result = run('mysql -V')
    if 'Ver 14.14 Distrib 5.7.17' not in result:
        # run('brew services stop mysql', warn_only=True)
        run('brew tap homebrew/services')
        run('brew install mysql')
        run('brew services start mysql')
        run('mysqladmin -u root password \'{dbpassword}\''.format(env.dbpassword))
        run('brew switch mysql 5.7.17')
        run('mysql_secure_installation')
        run('mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql')
        result = run('mysql -V')


@task
def install_mysql_linux():
    pass
