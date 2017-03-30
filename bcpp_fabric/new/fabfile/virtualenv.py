import os

from fabric.api import *
from fabric.contrib.console import confirm
from fabric.contrib.files import append

from .constants import LINUX, MACOSX


@task
def activate(name=None):
    run('source {}&&workon {}'.format(env.bash_profile, name))


@task
def mkvirtualenv(name=None, python_path=None, prompt=None):
    command = 'mkvirtualenv -p {} --no-site-packages {}'.format(
        python_path, name)
    run('source {}&&{}'.format(env.bash_profile, command))


@task
def rmvirtualenv(name=None, python_path=None, prompt=None):
    command = 'rmvirtualenv {}'.format(name, python_path)
    run('source {}&&{}'.format(env.bash_profile, command))


@task
def create_virtualenv(name=None, python_path=None, python_version=None,
                      target_os=None, prompt=None):
    """Makes the virtualenv on the remote host.
    """
    python_version = python_version or 3
    python_path = os.path.join(
        python_path or env.python_path, 'python{}'.format(str(python_version)))
    if prompt:
        if confirm('mkvirtualenv \'{}\'?'.format(name),
                   default=True):
            mkvirtualenv(name=name, python_path=python_path, prompt=prompt)
    else:
        mkvirtualenv(name=name, python_path=python_path, prompt=prompt)


@task
def install_virtualenvwrapper(target_os=None, prompt=None):
    """Installs virtualenvwrapper on the remote host.
    """
    LINUX_PATH = '/usr/share/virtualenvwrapper/'
    DARWIN_PATH = '/usr/local/bin/'
    target_os = target_os or env.target_os
    sudo('pip3 install virtualenvwrapper')
    if target_os == LINUX:
        path = os.path.join(LINUX_PATH, 'virtualenvwrapper.sh')
    elif target_os == MACOSX:
        path = os.path.join(DARWIN_PATH, 'virtualenvwrapper.sh')
    else:
        raise Exception('Unknown OS/System. Got \'{}\''.format(target_os))
    append(os.path.expanduser(os.path.join(env.bash_profile)),
           'export WORKON_HOME="$HOME/.virtualenvs"')
    append(os.path.expanduser(os.path.join(env.bash_profile)),
           'source {}'.format(path))
