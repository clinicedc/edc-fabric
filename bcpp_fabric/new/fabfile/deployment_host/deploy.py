import configparser
import os

from fabric.api import task, env, run, cd
from fabric.context_managers import lcd
from fabric.contrib.files import exists
from fabric.decorators import roles
from fabric.operations import put, local
from fabric.utils import abort

from ..constants import MACOSX
from ..environment import update_fabric_env
from ..repositories import get_repo_name
from ..utils import download_pip_archives, bootstrap_env

# NGINX_DIR = os.path.join(str(PurePath(BASE_DIR).parent), 'nginx_deployment')
# GUNICORN_DIR = NGINX_DIR
DEFAULT_DEPLOYMENT_ROOT = '~/deployment'


@task
@roles('deployment_hosts')
def prepare_deployment_host(bootstrap_path=None, release=None, use_branch=None,
                            skip_clone=None):
    """Prepares the deployment host.
    """
    bootstrap_env(bootstrap_path=bootstrap_path)
    env.project_repo_name = get_repo_name(env.project_repo_url)
    env.project_appname = env.project_repo_name.replace('-', '_')
    env.deployment_database_dir = os.path.join(env.deployment_root, 'database')
    env.deployment_dmg_dir = os.path.join(env.deployment_root, 'dmg')
    env.deployment_pip_dir = os.path.join(env.deployment_root, 'pip')
    env.deployment_download_dir = os.path.join(
        env.deployment_root, 'downloads')

    env.project_repo_root = os.path.join(
        env.deployment_root, env.project_repo_name)
    env.project_release = release

    env.fabric_config_root = os.path.join(env.project_repo_root, 'fabfile')
    env.fabric_config_path = os.path.join(
        env.project_repo_root, 'fabfile', 'conf', env.fabric_conf)
    prepare_deployment_dir()
    prepare_deployment_repo(skip_clone=skip_clone, use_branch=use_branch)
    if not exists(env.fabric_config_path):
        abort('Missing fabric config file. Expected {}'.format(
            env.fabric_config_path))
    update_env_secrets()
    update_fabric_env()
    put_python_package(path=env.downloads_dir)
    download_pip_archives()


def update_env_secrets(config_root=None):
    """Reads secrets into env from repo secrets_conf.gpg.
    """
    config_root = config_root or os.path.join(env.fabric_config_root, 'etc')
    secrets_conf_path = os.path.join(config_root, env.secrets_conf)
    if not exists(secrets_conf_path):
        abort('Not found {secrets_conf_gpg_path}'.format(
            secrets_conf_gpg_path=secrets_conf_path))
    with cd(config_root):
        config = decrypt_to_config(
            gpg_filename=env.secrets_conf, section='secrets')
        for key, value in config['secrets'].items():
            setattr(env, key, value)


def decrypt_to_config(gpg_filename=None, section=None):
    """Returns a config by decrypting a conf file with a single section.
    """
    section = '[{section}]'.format(section=section)
    conf_string = run('gpg --decrypt {gpg_filename}'.format(
        gpg_filename=gpg_filename))
    conf_string = conf_string.replace(
        'gpg: WARNING: message was not integrity protected', '\n')
    conf_string.split(section)[1]
    config = configparser.RawConfigParser()
    config.read_string('{section}\n{conf_string}\n'.format(
        section=section, conf_string=conf_string.split(section)[1]))
    return config


def prepare_deployment_dir():
    """Prepares a deployment folder.
    """
    if not exists(env.deployment_root):
        run('mkdir -p {dir}'.format(dir=env.deployment_root))
    if not exists(env.deployment_dmg_dir):
        run('mkdir {dir}'.format(dir=env.deployment_dmg_dir))
    if not exists(env.deployment_download_dir):
        run('mkdir {dir}'.format(dir=env.deployment_download_dir))
    if not exists(env.deployment_database_dir):
        run('mkdir {dir}'.format(dir=env.deployment_database_dir))


def prepare_deployment_repo(skip_clone=None, use_branch=None):
    if not env.project_release or (not use_branch and env.project_release in ['develop', 'master']):
        abort('Not deploying without a release version number (tag)')
    # clone project repo into deployment folder
    if not skip_clone:
        if exists(env.project_repo_root):
            run('rm -rf {}'.format(env.project_repo_root))
        with cd(env.deployment_root):
            run('git clone {project_repo_url}'.format(
                project_repo_url=env.project_repo_url))
    with cd(env.project_repo_root):
        run(
            'git checkout --force {release}'.format(release=env.project_release))


def put_python_package(path=None):
    """Puts the python package in the deployment downloads folder.

    If does not exist locally in ~/Downloads will download first.
    """
    local_path = os.path.expanduser(path)
    if env.target_os == MACOSX:
        if not os.path.exists(os.path.join(local_path, env.python_package)):
            with lcd(env.deployment_download_dir):
                local('wget {}'.format(env.python_package_url))
    put(os.path.join(local_path, env.python_package),
        os.path.join(env.deployment_download_dir, env.python_package))
