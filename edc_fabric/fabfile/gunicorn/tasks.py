import io
import plistlib
import os

from fabric.api import cd, env, run, task
from fabric.operations import put

from ..environment import bootstrap_env, update_fabric_env
from ..pip import pip_install_from_cache
from ..constants import MACOSX


@task
def install_gunicorn_task(bootstrap_path=None, local_fabric_conf=None,
                          bootstrap_branch=None, skip_bootstrap=None):
    if not skip_bootstrap:
        bootstrap_env(
            path=os.path.expanduser(bootstrap_path),
            bootstrap_branch=bootstrap_branch)
        update_fabric_env(use_local_fabric_conf=local_fabric_conf)
    install_gunicorn()


def install_gunicorn(work_online=None):
    if work_online:
        activate = os.path.join(env.venv_dir, env.venv_name, 'bin', 'activate')
        run(f'source {activate} && pip install -U gunicorn')
    else:
        pip_install_from_cache(package_name='gunicorn')
    with cd(env.log_root):
        run('touch gunicorn-access.log')
        run('touch gunicorn-error.log')
    if env.target_os == MACOSX:
        create_gunicorn_plist()


def create_gunicorn_plist(project_repo_name=None, user=None):
    project_repo_name = project_repo_name or env.project_repo_name
    user = env.user
    options = {
        'Label': 'gunicorn',
        'ProgramArguments': [
            'sh', os.path.join('/Users/{user}/source/{project_repo_name}'.format(
                user=user, project_repo_name=project_repo_name), 'gunicorn.sh')],
        'KeepAlive': True,
        'NetworkState': True,
        'RunAtLoad': False,
        'UserName': 'django'}
    plist = plistlib.dumps(options, fmt=plistlib.FMT_XML)
    put(io.BytesIO(plist), '/Library/LaunchDaemons/gunicorn.plist', use_sudo=True)
