import os

from fabric.api import env, run, cd, sudo, prefix
from fabric.contrib.files import append, contains, exists
from fabric.utils import abort

from ..pip import pip_install_from_cache, pip_install_requirements_from_cache

DEFAULT_VENV_DIR = '~/.venvs'
DEFAULT_VIRTUALENV_DIR = '~/.virtualenvs'


def install_virtualenv(venv_dir=None):
    """Installs virtualenvwrapper.
    """
    venv_dir = venv_dir or DEFAULT_VIRTUALENV_DIR
    if not exists(venv_dir):
        run('mkdir {venv_dir}'.format(venv_dir=venv_dir))
    lines = [
        'export WORKON_HOME=$HOME/{path}'.format(
            path=venv_dir.replace('~/', '')),
        'export PROJECT_HOME=$HOME/{path}'.format(
            path=env.remote_source_root.replace('~/', '')),
        'export VIRTUALENVWRAPPER_PYTHON=\'/usr/local/bin/python3\'',
        'source /usr/local/bin/virtualenvwrapper.sh']
    for line in lines:
        if not contains(env.bash_profile, line):
            append(env.bash_profile, line)
    run('source {path}'.format(path=env.bash_profile))
    with cd(env.deployment_pip_dir):
        sudo('pip3 install --no-index --find-links=. pip')
        sudo('pip3 install --no-index --find-links=. setuptools')
        sudo('pip3 install --no-index --find-links=. wheel')
        sudo('pip3 install --no-index --find-links=. virtualenv')
        sudo('pip3 install --no-index --find-links=. virtualenvwrapper')
        run('source /usr/local/bin/virtualenvwrapper.sh')


def make_virtualenv(venv_name=None, requirements_file=None):
    """Makes a virtualenv.
    """
    venv_dir = DEFAULT_VIRTUALENV_DIR
    venv_name = venv_name or env.venv_name
    requirements_file = requirements_file or env.requirements_file
    if exists(os.path.join(venv_dir, venv_name)):
        run('rmvirtualenv {venv_name}'.format(venv_name=venv_name))
    run('mkvirtualenv -p python3 --no-setuptools --no-pip --no-wheel {venv_name}'.format(
        venv_name=env.venv_name,
        deployment_pip_dir=env.deployment_pip_dir), warn_only=True)
    with prefix('workon {venv_name}'.format(venv_name=venv_name)):
        result = run('python --version')
        if env.python_version not in result:
            abort(result)
    pip_install_from_cache(package_name='pip')
    pip_install_from_cache(package_name='setuptools')
    pip_install_from_cache(package_name='wheel')
    pip_install_from_cache(package_name='ipython')
    pip_install_requirements_from_cache()


def activate_venv():
    return os.path.join(env.venv_dir, env.venv_name, 'bin', 'activate')


def create_venv(venv_name=None, requirements_file=None, work_online=None):
    """Makes a python3.6 venv.
    """
    venv_name = venv_name or env.venv_name
    requirements_file = requirements_file or env.requirements_file
    if not exists(env.venv_dir):
        run(f'mkdir {env.venv_dir}')
    if exists(os.path.join(env.venv_dir, venv_name)):
        run('rm -rf {path}'.format(path=os.path.join(env.venv_dir, venv_name)))
    with cd(env.venv_dir):
        run('python3.6 -m venv --clear --copies {venv_name} {path}'.format(
            path=os.path.join(env.venv_dir, venv_name), venv_name=venv_name),
            warn_only=True)
    text = 'workon () {{ source {activate}; }}'.format(
        activate=os.path.join(env.venv_dir, '"$@"', 'bin', 'activate'))
    if not contains(env.bash_profile, text):
        append(env.bash_profile, text)
    if work_online:
        run(f'source {activate_venv()} && pip install -U pip setuptools wheel ipython')
        with cd(env.project_repo_root):
            run(f'source {activate_venv()} && pip install -U -r {env.requirements_file}')

    else:
        pip_install_from_cache('pip')
        pip_install_from_cache('setuptools')
        pip_install_from_cache('wheel')
        pip_install_from_cache('ipython')
        pip_install_requirements_from_cache()
