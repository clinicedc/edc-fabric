import os

from fabric.api import execute, task, env, run, cd, sudo, prefix
from fabric.contrib.files import exists

from .apache import disable_apache
from .constants import LINUX, MACOSX
from .env import update_fabric_env
from .repositories import get_repo, get_repo_name
from .utils import install_python3

# NGINX_DIR = os.path.join(str(PurePath(BASE_DIR).parent), 'nginx_deployment')
# GUNICORN_DIR = NGINX_DIR


@task
def prepare_deploy(config_path=None, user=None, target_os=None,
                   clear_venv=None, update_environment=None):
    """Prepares the remote host(s) env for deployment.
    """
    clear_venv = True if clear_venv is None else clear_venv
    update_environment = True if update_environment is None else update_environment
    if update_environment:
        update_fabric_env(fabric_config_path=config_path)
    update_fabric_env(fabric_config_path=config_path)
    env.user = user or env.user
    env.target_os = target_os or env.target_os
    env.project_repo_name = get_repo_name(env.project_repo_url)
    python3_path = run("which python3", quiet=True)
    if env.target_os == LINUX:
        sudo('apt-get install python-crypto python-cups python3-dev libssl-dev libcups2-dev')
    if env.target_os == MACOSX:
        if not python3_path:
            install_python3()
    with cd('~/'):
        if not exists(env.remote_source_root):
            run('mkdir -p {name}'.format(name=env.remote_source_root))
        if not exists(env.deployment_root):
            run('mkdir -p {name}'.format(name=env.deployment_root))
    sudo('pip3 install -U pip')
    execute(create_venv, name=env.venv_name, clear_venv=clear_venv)
    execute(disable_apache)
    with cd(env.remote_source_root):
        execute(get_repo,
                repo_url=env.project_repo_url,
                repo_name=env.project_repo_name,
                local_root=env.local_source_root,
                remote_root=env.remote_source_root)


@task
def deploy(config_path=None, user=None, target_os=None, project_repo_url=None, update_environment=None):
    """Deploys the project to the remote host(s).
    """
    update_environment = True if update_environment is None else update_environment
    if update_environment:
        update_fabric_env(fabric_config_path=config_path)
    env.user = user or env.user
    env.target_os = target_os or env.target_os
    project_repo_url = project_repo_url or env.project_repo_url
    project_repo_name = get_repo_name(project_repo_url)
    project_repo_dir = os.path.join(
        env.remote_source_root, project_repo_name)
    with cd(project_repo_dir):
        with prefix('workon {}'.format(env.venv_name)):
            if env.update_requirements:
                run('pip3 install -U -r requirements.txt')
            if env.update_collectstatic:
                run('python manage.py collectstatic')
            if env.update_collectstatic_js_reverse:
                run('python manage.py collectstatic_js_reverse')

        # etc ...in progress
        # put(local_dir, remote_dir, use_sudo)()
