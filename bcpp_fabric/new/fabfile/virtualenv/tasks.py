import configparser
import csv
import os
import re

from fabric.api import env, local, run, cd, sudo, task, warn
from fabric.colors import red
from fabric.contrib.files import append, contains, exists
from fabric.utils import abort

from ..constants import LINUX, MACOSX
from ..env import update_fabric_env, bootstrap_env
from ..pip import pip_install_from_cache, pip_install_requirements_from_cache

# sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.locate.plist


def install_virtualenv(venv_dir=None):
    if not exists(venv_dir):
        run('mkdir {venv_dir}'.format(venv_dir=venv_dir))
    lines = [
        'export WORKON_HOME=$HOME/{path}'.format(
            path=venv_dir.replace('~/', '')),
        'export PROJECT_HOME=$HOME/{path}'.format(
            path=env.remote_source_root.replace('~/', '')),
        'export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python',
        'source /usr/local/bin/virtualenvwrapper.sh']
    for line in lines:
        if not contains(env.bash_profile, line):
            append(env.bash_profile, line)
    run('source {path}'.format(path=env.bash_profile))
    with cd(env.deployment_pip_dir):
        sudo('pip install --no-index --find-links=. pip')
        sudo('pip install --no-index --find-links=. setuptools')
        sudo('pip install --no-index --find-links=. wheel')
        sudo('pip install --no-index --find-links=. virtualenv')
        sudo('pip install --no-index --find-links=. virtualenvwrapper')
        run('source /usr/local/bin/virtualenvwrapper.sh')


def create_virtualenv(name=None, venv_dir=None, clear_venv=None, create_env=None,
                      update_requirements=None, requirements_file=None):
    """Makes the venv.
    """
    venv_dir = venv_dir or '~/.virtualenvs'
    create_env = create_env if create_env is not None else env.create_env
    update_requirements = update_requirements if update_requirements is not None else env.update_requirements
    requirements_file = requirements_file or env.requirements_file
    if not create_env:
        if not exists(os.path.join(venv_dir, name)):
            abort('{}. virtualenv does not exist!'.format(env.host))
    else:
        install_virtualenv(venv_dir=venv_dir)
        if exists(os.path.join(venv_dir, name)):
            run('rmvirtualenv {name}'.format(name=name))
        run('mkvirtualenv {name} -p python3 --no-setuptools --no-pip --no-wheel'.format(
            name=name,
            deployment_pip_dir=env.deployment_pip_dir), warn_only=True)
        result = run('workon bcpp && python --version', warn_only=True)
        if env.python_version not in result:
            abort(result)
        pip_install_from_cache('pip')
        pip_install_from_cache('setuptools')
        pip_install_from_cache('wheel')
        pip_install_from_cache('ipython')
        pip_install_requirements_from_cache()


def create_venv(name=None, venv_dir=None, clear_venv=None, create_env=None,
                update_requirements=None, requirements_file=None):
    """Makes a python3 venv.
    """
    venv_dir = venv_dir or '~/.venv'
    create_env = create_env if create_env is not None else env.create_env
    update_requirements = update_requirements if update_requirements is not None else env.update_requirements
    requirements_file = requirements_file or env.requirements_file
    if not create_env:
        if not exists(os.path.join(venv_dir, name)):
            abort('{}. venv does not exist!'.format(env.host))
    else:
        if not exists(venv_dir):
            run('mkdir {venv_dir}'.format(venv_dir=venv_dir))
        if exists(os.path.join(venv_dir, name)):
            run('rm -rf {path}'.format(path=os.path.join(venv_dir, name)))
        with cd(venv_dir):
            if clear_venv or not exists(os.path.join(venv_dir, name)):
                run('python3 -m venv --clear {path} {name}'.format(path=os.path.join(venv_dir, name), name=name),
                    warn_only=True)
        text = 'workon () {{ source {activate}; }}'.format(
            activate=os.path.join(venv_dir, '"$@"', 'bin', 'activate'))
        if not contains(env.bash_profile, text):
            append(env.bash_profile, text)
        pip_install_from_cache('pip')
        pip_install_from_cache('setuptools')
        pip_install_from_cache('wheel')
        pip_install_from_cache('ipython')
        pip_install_requirements_from_cache()
