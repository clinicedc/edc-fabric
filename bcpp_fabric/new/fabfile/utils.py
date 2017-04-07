import configparser
import csv
import os
import re

from fabric.api import env, local, run, cd, sudo, task, warn
from fabric.colors import red
from fabric.contrib.files import contains
from fabric.utils import abort

from .constants import LINUX, MACOSX
from .env import update_fabric_env, bootstrap_env

# sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.locate.plist


def install_python3(python_version=None):
    """Installs python3.
    """
    python_version = python_version or env.python_version
    if env.target_os == MACOSX:
        run('brew install python3', warn_only=True)
    elif env.target_os == LINUX:
        sudo('apt-get install python3-pip ipython3 python3={}*'.format(python_version))


def install_gpg(path=None):
    """Installs gpg.
    """
    if env.target_os == MACOSX:
        run('brew install gnupg gnupg2')
    elif env.target_os == LINUX:
        sudo('apt-get install gnupg gnupg2')


def check_deviceids(app_name=None):
    """Checks remote device id against conf dictionary.

    Aborts on first error.
    """
    app_name = app_name or env.project_appname
    remote_path = os.path.join(
        env.remote_source_root, env.project_appname, app_name)
    for host, device_id in env.device_ids.items():
        with cd(remote_path):
            if not contains('settings.py', 'DEVICE_ID = {}'.format(device_id)):
                abort(red('{} Incorrect device id. Expected {}.'.format(
                    host, device_id)))
#                 fd = StringIO()
#                 get(os.path.join(remote_path, 'settings.py'), fd)
#                 content = fd.getvalue()
#                 print('content', content)


def get_hosts(path=None, gpg_filename=None):
    """Returns a list of hostnames extracted from the hosts.conf.gpg.

    Does nothing if env.hosts is already set.
    """
    # see also roledefs
    hosts = []
    passwords = {}

    if env.roles:
        for role in env.roles:
            env.hosts.extend(env.roledefs.get(role) or [])
    conf_string = local('cd {path}&&gpg2 --decrypt {gpg_filename}'.format(
        path=path, gpg_filename=gpg_filename), capture=True)
    conf_string = conf_string.replace(
        'gpg: WARNING: message was not integrity protected', '\n')
    conf_data = conf_string.split('\n')
    csv_reader = csv.reader(conf_data)

    if env.hosts:
        for index, row in enumerate(csv_reader):
            if index == 0:
                continue
            else:
                if row[0] in env.hosts:
                    host = '{user}@{hostname}:22'.format(
                        user=env.user or 'django', hostname=row[0])
                    env.passwords.update({host: row[1]})
    else:
        conf_string = local('cd {path}&&gpg2 --decrypt {gpg_filename}'.format(
            path=path, gpg_filename=gpg_filename), capture=True)
        conf_string = conf_string.replace(
            'gpg: WARNING: message was not integrity protected', '\n')
        conf_data = conf_string.split('\n')
        csv_reader = csv.reader(conf_data)
        for index, row in enumerate(csv_reader):
            if index == 0:
                continue
            hosts.append(row[0])
            host = '{user}@{hostname}:22'.format(
                user=env.user or 'django', hostname=row[0])
            passwords.update({host: row[1]})
    if env.hosts:
        return (env.hosts, env.passwords)
    else:
        return (hosts, passwords)


def get_device_ids(hostname_pattern=None):
    """Returns a list of device IDS based on the hostnames.

    env.hosts must be set first.
    """
    device_ids = {}
    hostname_pattern = hostname_pattern or env.hostname_pattern
    for hostname in env.hosts:
        if (hostname not in env.roledefs.get('deployment_hosts')
                and hostname not in env.roledefs.get('servers', [])):
            if not re.match(hostname_pattern, hostname):
                warn('Invalid hostname. Cannot determine device ID. Ignoring. Got {hostname}'.format(
                    hostname=hostname))
            else:
                device_ids.update({hostname: hostname[-2:]})
    if len(list(set(device_ids))) != len(device_ids):
        abort('Device ID list not unique.')
    return device_ids


def get_archive_name():
    """Returns the name of the deployment archive.
    """
    return '{project_appname}.{release}.tar.bz2'.format(
        project_appname=env.project_appname, release=env.project_release)


def cut_releases(source_root_path=None):
    source_root_path = source_root_path or '~/source'


def decrypt_to_config(gpg_filename=None, section=None):
    """Returns a config by decrypting a conf file with a single section.
    """
    section = '[{section}]'.format(section=section)
    conf_string = run('gpg2 --decrypt {gpg_filename}'.format(
        gpg_filename=gpg_filename))
    conf_string = conf_string.replace(
        'gpg: WARNING: message was not integrity protected', '\n')
    conf_string.split(section)[1]
    config = configparser.RawConfigParser()
    config.read_string('{section}\n{conf_string}\n'.format(
        section=section, conf_string=conf_string.split(section)[1]))
    return config


@task
def test_connection(config_path=None, local_fabric_conf=None, bootstrap_branch=None):
    bootstrap_env(
        path=os.path.expanduser(os.path.join(config_path, 'conf')),
        bootstrap_branch=bootstrap_branch)
    update_fabric_env(use_local_fabric_conf=local_fabric_conf)
    result_os = run('sw_vers -productVersion')
    result_mysql = run('mysql -V', warn_only=True)
    result_nginx = run('nginx -V', warn_only=True)
    with open(os.path.join(env.log_folder, '{host}.txt'.format(host=env.host)), 'a') as f:
        if env.os_version not in result_os:
            warn('{} OSX outdated. Got {}'.format(env.host, result_os))
        f.write('{host} OSX {result}\n'.format(
            host=env.host, result=result_os))
        if env.mysql_version not in result_mysql:
            warn('{} MYSQL outdated. Got {}'.format(env.host, result_mysql))
        f.write('{host} MYSQL {result}\n'.format(
            host=env.host, result=result_mysql))
        if env.nginx_version not in result_nginx:
            warn('{} NGINX outdated. Got {}'.format(env.host, result_nginx))
        f.write('{host} NGINX {result}\n'.format(
            host=env.host, result=result_nginx.split('\n')[0]))


@task
def gpg(config_path=None, label=None):
    run('brew install gnupg gnupg2')
#     # 'Warning: gnupg-2.1.19 already installed'
#     with open(os.path.expanduser('~/deployment/osx.txt'), 'a') as f:
#         if 'gnupg-2.1.19' not in result_os:
#             warn('{} OSX outdated. Got {}'.format(env.host, result_os))
#         f.write('{label}: {host} OSX {result}\n'.format(
#             label=label, host=env.host, result=result_os))
#         f.write('{label}: {host} MYSQL {result}\n'.format(
#             label=label, host=env.host, result=result_mysql))


@task
def ssh_copy_id():
    pub_key = local('cat ~/.ssh/id_rsa.pub', capture=True)
    with cd('~/.ssh'):
        run('touch authorized_keys')
        result = run('cat authorized_keys', quiet=True)
        if pub_key not in result:
            run('cp authorized_keys authorized_keys.bak')
            run('echo {} >> authorized_keys'.format(pub_key))
