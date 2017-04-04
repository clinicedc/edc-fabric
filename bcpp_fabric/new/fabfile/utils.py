import csv
import os
import re

from io import StringIO

from fabric.api import env, prefix, local, run, cd, sudo, get
from fabric.colors import red
from fabric.contrib.files import append, contains, exists
from fabric.utils import abort

from .constants import LINUX, MACOSX
from pathlib import PurePath
import configparser

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
                run('python3 -m venv --clear {path}'.format(path=os.path.join(venv_dir, name)),
                    warn_only=True)
        with prefix('source {activate}'.format(activate=os.path.join(venv_dir, name, 'bin', 'activate'))):
            run('pip install -U pip ipython')
        if update_requirements:
            with cd(env.project_repo_root):
                with prefix('source {activate}'.format(activate=os.path.join(venv_dir, name, 'bin', 'activate'))):
                    run('pip3 install -U -r {requirements_file}'.format(
                        requirements_file=requirements_file))


def install_venv(venv_name=None, venv_dir=None):
    venv_dir = venv_dir or DEFAULT_VENV_DIR
    if not exists(os.path.join(env.deployment_root, 'venv')):
        abort('venv folder missing. Have you deployed the tarball yet?')
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
    """
    # see also roledefs
    hosts = []
    conf_string = local('cd {path}&&gpg --decrypt {gpg_filename}'.format(
        path=path, gpg_filename=gpg_filename), capture=True)
    conf_string = conf_string.replace(
        'gpg: WARNING: message was not integrity protected', '\n')
    conf_data = conf_string.split('\n')
    csv_reader = csv.reader(conf_data)
    for index, row in enumerate(csv_reader):
        if index == 0:
            continue
        hosts.append(row[0])
    return hosts


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
                abort('Invalid hostname. Got {hostname}'.format(hostname))
            device_ids.append(hostname[-2:])
    if len(list(set(device_ids))) != len(device_ids):
        abort('Device ID list not unique.')
    return device_ids


def download_pip_archives():
    """Downloads pip archives into deployment pip dir.
    """
    if exists(env.deployment_pip_dir):
        run('rm -rf {deployment_pip_dir}'.format(
            deployment_pip_dir=env.deployment_pip_dir))
        run('mkdir -p {deployment_pip_dir}'.format(
            deployment_pip_dir=env.deployment_pip_dir))
    with cd(env.project_repo_root):
        run('pip download --python-version 3 --only-binary=:all: '
            '-d {deployment_pip_dir} -r {requirements}'.format(
                deployment_pip_dir=env.deployment_pip_dir,
                requirements=env.requirements_file))


def get_archive_name(deployment_root=None, release=None):
    """Returns the name of the deployment archive.
    """
    path = PurePath(env.deployment_root).parts[-1:][0]
    return '{path}.{release}.tar.bz2'.format(path=path, release=release)


def bootstrap_env(bootstrap_path=None):
    """Bootstraps env.
    """
    config = configparser.RawConfigParser()
    config.read(os.path.expanduser(bootstrap_path))
    env.downloads_dir = config['bootstrap']['downloads_dir']
    env.target_os = config['bootstrap']['target_os']
    env.project_repo_url = config['bootstrap']['project_repo_url']
    env.deployment_root = config['bootstrap']['deployment_root']
    env.requirements_file = config['bootstrap']['requirements_file']
    env.fabric_conf = 'fabric.conf'
    env.hosts_conf = 'hosts.conf.gpg'
    env.secrets_conf = 'secrets.conf.gpg'
