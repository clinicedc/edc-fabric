import os

from pathlib import PurePath

from fabric.api import task, env, run, cd
from fabric.context_managers import lcd
from fabric.contrib.files import exists
from fabric.operations import put, local
from fabric.utils import abort

from ..constants import MACOSX
from ..environment import update_fabric_env
from ..utils import bootstrap_env, get_archive_name

# NGINX_DIR = os.path.join(str(PurePath(BASE_DIR).parent), 'nginx_deployment')
# GUNICORN_DIR = NGINX_DIR
DEFAULT_DEPLOYMENT_ROOT = '~/deployment'


@task
def prepare_deployment_host(bootstrap_path=None, release=None, use_branch=None,
                            skip_clone=None, bootstrap_branch=None, skip_pip_download=None):
    """Prepares the deployment host.
    """
    bootstrap_env(
        path=bootstrap_path,
        filename='bootstrap.conf',
        bootstrap_branch=bootstrap_branch)
    if release:
        env.project_release = release
    prepare_deployment_dir()
    prepare_deployment_repo(skip_clone=skip_clone, use_branch=use_branch)
    if not exists(env.fabric_config_path):
        abort('Missing fabric config file. Expected {}'.format(
            env.fabric_config_path))
    update_fabric_env()
    put_python_package(path=env.downloads_dir)
    if env.target_os == MACOSX and not skip_pip_download:
        pip_download_cache()
    create_deployment_archive()


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
        abort('Not deploying without a release version number (tag). '
              'Got env.project_release={project_release} and '
              'use_branch={use_branch}'.format(
                  project_release=env.project_release,
                  use_branch=use_branch))
    # clone project repo into deployment folder
    if not skip_clone:
        if exists(env.project_repo_root):
            run('rm -rf {}'.format(env.project_repo_root))
        with cd(env.deployment_root):
            run('git clone {project_repo_url}'.format(
                project_repo_url=env.project_repo_url))
    with cd(env.project_repo_root):
        run('git checkout --force {release}'.format(
            release=env.project_release))


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


def pip_download_cache():
    """Downloads pip packages into deployment pip dir.
    """
    if exists(env.deployment_pip_dir):
        run('rm -rf {deployment_pip_dir}'.format(
            deployment_pip_dir=env.deployment_pip_dir))
        run('mkdir -p {deployment_pip_dir}'.format(
            deployment_pip_dir=env.deployment_pip_dir))
    with cd(env.project_repo_root):
        # can't use
        # run('pip download --python-version 3 --only-binary=:all: '
        # as not all packages have a wheel (arrow, etc)
        run('pip download '
            '-d {deployment_pip_dir} -r {requirements}'.format(
                deployment_pip_dir=env.deployment_pip_dir,
                requirements=env.requirements_file), warn_only=True)


def create_deployment_archive():
    archive_name = get_archive_name()
    with cd(str(PurePath(env.deployment_root).parent)):
        run('tar -cjf {archive_name} {project_appname}'.format(
            archive_name=archive_name,
            project_appname=env.project_appname))
