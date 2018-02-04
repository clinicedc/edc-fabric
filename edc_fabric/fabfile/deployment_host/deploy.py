from fabric.api import task, env, run, cd, warn
from fabric.contrib.files import exists
from fabric.utils import abort

from ..brew import update_deployment_brew_dir
from ..constants import MACOSX
from ..environment import update_fabric_env
from ..pip import pip_download_cache
from ..utils import bootstrap_env

# NGINX_DIR = os.path.join(str(PurePath(BASE_DIR).parent), 'nginx_deployment')
# GUNICORN_DIR = NGINX_DIR
DEFAULT_DEPLOYMENT_ROOT = '~/deployment'


@task
def prepare_deployment_host(bootstrap_path=None, release=None, use_branch=None,
                            skip_clone=None, bootstrap_branch=None,
                            skip_pip_download=None, skip_brew_download=None,
                            specific_tag=None):
    """Prepares the deployment host.
    """
    bootstrap_env(
        path=bootstrap_path,
        filename='bootstrap.conf',
        bootstrap_branch=bootstrap_branch)
    if release:
        env.project_release = release
    prepare_deployment_dir()
    prepare_deployment_repo(skip_clone=skip_clone, use_branch=use_branch,
                            specific_tag=specific_tag)
    with cd(env.project_repo_root):
        result = run('git status', warn_only=True)
        results = result.split('\n')
        if results[0] != 'On branch {bootstrap_branch}'.format(
                bootstrap_branch=bootstrap_branch):
            warn(results[0])
    if not exists(env.fabric_config_path):
        abort('Missing fabric config file. Expected {}'.format(
            env.fabric_config_path))
    update_fabric_env()
    if env.target_os == MACOSX and not skip_pip_download:
        pip_download_cache()
    if env.target_os == MACOSX and not skip_brew_download:
        update_deployment_brew_dir()


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
    if not exists(env.deployment_pip_dir):
        run('mkdir {dir}'.format(dir=env.deployment_pip_dir))
    if not exists(env.deployment_brew_dir):
        run('mkdir {dir}'.format(dir=env.deployment_brew_dir))


def prepare_deployment_repo(skip_clone=None, specific_tag=None, use_branch=None):
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
        if specific_tag:
            with cd(env.project_repo_root):
                run(f'git checkout {env.project_release}')
#     with cd(env.project_repo_root):
#         run('git checkout {release}'.format(
#             release=env.project_release), warn_only=True)
