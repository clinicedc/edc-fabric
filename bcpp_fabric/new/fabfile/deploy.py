import os

from pathlib import PurePath

from fabric.api import *
from fabric.contrib.files import exists
from fabric.contrib.project import upload_project

# from .databases import DATABASE_FILES
# from .hosts import HOSTS
# from .repo_list import REPOS

from .apache import disable_apache
from .constants import LINUX
from .environment import update_env
from .repositories import get_repo, clone_required_repos, get_repo_name
from .virtualenv import create_virtualenv, install_virtualenvwrapper, rmvirtualenv

BASE_DIR = str(PurePath(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))).parent)
CONFIG_FILENAME = 'config.conf'
# NGINX_DIR = os.path.join(str(PurePath(BASE_DIR).parent), 'nginx_deployment')
# GUNICORN_DIR = NGINX_DIR


@task
def prepare_local_deploy(config_path=None, target_os=None, prompt=None):
    """Clones all project required repos locally into
    the deployment folder.

    This is only needed if you are clone/rsyncing from offline
    repositories.
    """
    update_env(config_path=config_path or os.path.join(
        BASE_DIR, CONFIG_FILENAME))
    env.target_os = env.target_os or target_os
    execute(clone_required_repos)


@task
def prepare_deploy(config_path=None, user=None, target_os=None, prompt=None, remove_virtualenv=None):
    """Prepares the remote host(s) env for deployment.
    """
    update_env(config_path=config_path or os.path.join(
        BASE_DIR, CONFIG_FILENAME))
    env.user = user or env.user
    env.target_os = target_os or env.target_os
    with cd('~/'):
        if not exists('~/source'):
            run('mkdir -p ~/source')
    if env.target_os == LINUX:
        sudo('apt-get install python3-pip ipython3')
    run('pip3 install -U pip ipython')
    execute(install_virtualenvwrapper, target_os=env.target_os, prompt=prompt)
    if remove_virtualenv:
        execute(rmvirtualenv,
                name=env.virtualenv_name,
                python_path=env.python_path,
                prompt=prompt)
    execute(create_virtualenv,
            name=env.virtualenv_name,
            python_path=env.python_path,
            python_version=env.python_version,
            target_os=env.target_os,
            prompt=prompt)
    execute(disable_apache, prompt=prompt)
    with cd('~/source'):
        execute(get_repo,
                repo_url=env.project_repo_url,
                repo_name=env.project_repo_name,
                local_root=env.local_source_root,
                remote_root=env.remote_source_root,
                prompt=prompt)
    if env.target_os == LINUX:
        sudo('apt-get install python-crypto python-cups python3-dev libssl-dev libcups2-dev')


@task
def deploy(config_path=None, user=None, target_os=None, project_repo_url=None, prompt=None):
    """Deploys the project to the remote host(s).
    """
    update_env(config_path=config_path or os.path.join(
        BASE_DIR, CONFIG_FILENAME))
    env.user = user or env.user
    env.target_os = target_os or env.target_os
    project_repo_url = project_repo_url or env.project_repo_url
    with prefix('source {}&&workon {}'.format(env.bash_profile, env.virtualenv_name)):
        project_repo_name = get_repo_name(project_repo_url)
        project_repo_dir = os.path.join(
            env.remote_source_root, project_repo_name)
        with cd(project_repo_dir):
            run('pip3 install -U -r requirements.txt')

        # etc ...in progress
        # put(local_dir, remote_dir, use_sudo)()
