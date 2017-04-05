import configparser
import csv
import os
import re

from datetime import datetime
from io import StringIO

from fabric.api import env, prefix, local, run, cd, sudo, get, task, warn
from fabric.colors import red
from fabric.contrib.files import append, contains, exists
from fabric.utils import abort

from .constants import LINUX, MACOSX
from .repositories import get_repo_name

# sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.locate.plist

DEFAULT_VENV_DIR = '~/.venv'


def create_venv(name=None, venv_dir=None, clear_venv=None, create_env=None,
                update_requirements=None, requirements_file=None):
    """Makes the venv.
    """
    venv_dir = venv_dir or DEFAULT_VENV_DIR
    create_env = create_env if create_env is not None else env.create_env
    update_requirements = update_requirements if update_requirements is not None else env.update_requirements
    requirements_file = requirements_file or env.requirements_file
    if not create_env:
        if not exists(os.path.join(venv_dir, name)):
            abort('{}. venv does not exist!'.format(env.host))
    else:
        if not exists(venv_dir):
            run('mkdir {venv_dir}'.format(venv_dir=venv_dir))
        with cd(venv_dir):
            if clear_venv or not exists(os.path.join(venv_dir, name)):
                run('python3 -m venv --clear {path} {name}'.format(path=os.path.join(venv_dir, name), name=name),
                    warn_only=True)
        with prefix('source {activate}'.format(activate=os.path.join(venv_dir, name, 'bin', 'activate'))):
            run('pip3 install -U pip setuptools wheel ipython')
        if update_requirements:
            with cd(env.project_repo_root):
                with prefix('source {activate}'.format(activate=os.path.join(venv_dir, name, 'bin', 'activate'))):
                    run('pip3 install -U -r {requirements_file}'.format(
                        requirements_file=requirements_file))


def install_venv(venv_name=None, venv_dir=None):
    venv_dir = venv_dir or DEFAULT_VENV_DIR
    if not exists(venv_dir):
        run('mkdir {venv_dir}'.format(venv_dir=venv_dir))
    if exists('~/.virtualenvs'):
        run('rm -rf path'.format(path=os.path.join('~/.virtualenvs', venv_name)))
        run('pip uninstall virtualenvwrapper')
        run('pip uninstall virtualenv')
    if exists(os.path.join(venv_dir, venv_name)):
        run('rm -rf {path}'.format(path=os.path.join(venv_dir, venv_name)))
    with cd(env.deployment_root):
        run('cp -r venv/{venv_name}/ {path}'.format(
            venv_name=venv_name,
            path=os.path.join(venv_dir, venv_name)))
    text = 'workon () {{ source {activate}; }}'.format(
        activate=os.path.join(venv_dir, '"$@"', 'bin', 'activate'))
    if not contains(env.bash_profile, text):
        append(env.bash_profile, text)


def install_python3(python_version=None):
    """Installs python3.
    """
    python_version = python_version or env.python_version
    if env.target_os == MACOSX:
        python_package = env.python_package
        with cd(env.deployment_download_dir):
            sudo('installer -pkg {} -target /'.format(python_package))
    elif env.target_os == LINUX:
        sudo('apt-get install python3-pip ipython3 python3={}*'.format(python_version))


def install_gpg(path=None):
    """Installs gpg from a DMG.
    """
    if env.target_os == MACOSX:
        with cd(env.deployment_download_dir):
            result = sudo('hdiutil attach {gpg_dmg}'.format(
                gpg_dmg=env.gpg_dmg))
            mountpoint = [
                i.strip() for i in result.split('\n')[-1:][0].split('\t')][-1:][0]
            mountpoint = mountpoint.replace(' ', '\ ')
            result = run('ls -la {}'.format(mountpoint))
            sudo('installer -pkg {path} -target /'.format(
                path=os.path.join('/Volumes', mountpoint, 'Install.pkg')))
            run('hdiutil detach {path}'.format(
                path=os.path.join('/Volumes', mountpoint)), warn_only=True)
    elif env.target_os == LINUX:
        pass
        # sudo('apt-get install python3-pip ipython3 python3={}*'.format(python_version))


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
    device_ids = []
    hostname_pattern = hostname_pattern or env.hostname_pattern
    for hostname in env.hosts:
        if (hostname not in env.roledefs.get('deployment_hosts')
                and hostname not in env.roledefs.get('servers', [])):
            if not re.match(hostname_pattern, hostname):
                warn('Invalid hostname. Got {hostname}'.format(
                    hostname=hostname))
            else:
                device_ids.append(hostname[-2:])
    if len(list(set(device_ids))) != len(device_ids):
        abort('Device ID list not unique.')
    return device_ids


def pip_install_from_cache():
    """pip installs required packages from the local cache.
    """
    package_names = get_required_package_names()
    for package_name in package_names:
        with cd(env.deployment_pip_dir):
            with prefix('source {}'.format(os.path.join(env.venv_dir, env.venv_name, 'bin', 'activate'))):
                run('pip3 install --no-index --find-links=. {package_name}'.format(
                    package_name=package_name))


def get_required_package_names():
    package_names = []
    with cd(env.project_repo_root):
        data = run('cat {requirements}'.format(
            requirements=env.requirements_file))
        data = data.split('\n')
        for line in data:
            if 'botswana-harvard' in line or 'erikvw' in line:
                repo_url = line.split('@')[0].replace('git+', '')
                package_names.append(get_repo_name(repo_url))
    return package_names


def get_archive_name():
    """Returns the name of the deployment archive.
    """
    return '{project_appname}.{release}.tar.bz2'.format(
        project_appname=env.project_appname, release=env.project_release)


def bootstrap_env(path=None, filename=None):
    """Bootstraps env.
    """
    path = os.path.join(os.path.expanduser(path), filename or 'bootstrap.conf')
    config = configparser.RawConfigParser()
    config.read(os.path.expanduser(path))
    env.deployment_download_dir = config['bootstrap']['deployment_download_dir']
    env.downloads_dir = config['bootstrap']['downloads_dir']
    env.target_os = config['bootstrap']['target_os']
    env.project_repo_url = config['bootstrap']['project_repo_url']
    env.deployment_root = config['bootstrap']['deployment_root']
    env.requirements_file = config['bootstrap']['requirements_file']
    env.project_appname = config['bootstrap']['project_appname']
    env.fabric_conf = 'fabric.conf'
    env.hosts_conf = 'hosts.conf.gpg'
    env.secrets_conf = 'secrets.conf.gpg'


def cut_releases(source_root_path=None):
    source_root_path = source_root_path or '~/source'


def update_env_secrets(path=None):
    """Reads secrets into env from repo secrets_conf.
    """
    path = os.path.expanduser(path)
    secrets_conf_path = os.path.join(path, 'secrets.conf')
    if not os.path.exists(secrets_conf_path):
        abort('Not found {secrets_conf_gpg_path}'.format(
            secrets_conf_gpg_path=secrets_conf_path))
    config = configparser.RawConfigParser()
    with open(secrets_conf_path, 'r') as f:
        data = f.read()
    config.read_string(data)
    for key, value in config['secrets'].items():
        setattr(env, key, value)


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
def test_connection(config_path=None, label=None):
    result_os = run('sw_vers -productVersion')
    result_mysql = run('mysql -V')
    with open(os.path.expanduser(env.log_filename), 'a') as f:
        if env.os_version not in result_os:
            warn('{} OSX outdated. Got {}'.format(env.host, result_os))
        f.write('{label}: {host} OSX {result}\n'.format(
            label=label, host=env.host, result=result_os))
        f.write('{label}: {host} MYSQL {result}\n'.format(
            label=label, host=env.host, result=result_mysql))


@task
def gpg(config_path=None, label=None):
    result = run('brew install gnupg gnupg2')
#     # 'Warning: gnupg-2.1.19 already installed'
#     with open(os.path.expanduser('~/deployment/osx.txt'), 'a') as f:
#         if 'gnupg-2.1.19' not in result_os:
#             warn('{} OSX outdated. Got {}'.format(env.host, result_os))
#         f.write('{label}: {host} OSX {result}\n'.format(
#             label=label, host=env.host, result=result_os))
#         f.write('{label}: {host} MYSQL {result}\n'.format(
#             label=label, host=env.host, result=result_mysql))
