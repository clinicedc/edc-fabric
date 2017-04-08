import io
import plistlib
import os

from fabric.api import cd, env, run
from fabric.operations import put
from ..pip import pip_install_from_cache


def install_gunicorn():
    pip_install_from_cache(package_name='gunicorn')
    with cd(env.log_root):
        run('touch gunicorn-access.log')
        run('touch gunicorn-error.log')
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
