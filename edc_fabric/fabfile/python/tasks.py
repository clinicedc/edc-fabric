from fabric.api import env, run, sudo, abort, prefix

from ..constants import MACOSX, LINUX


def install_python3(python_version=None):
    """Installs python3.
    """
    python_version = python_version or env.python_version
    if env.target_os == MACOSX:
        with prefix('export HOMEBREW_NO_AUTO_UPDATE=1'):
            result = run('brew install python3', warn_only=True)
            if 'Error' in result:
                run('rm /usr/local/bin/idle3')
                run('rm /usr/local/bin/pydoc3')
                run('rm /usr/local/bin/python3')
                run('rm /usr/local/bin/python3-config')
                run('rm /usr/local/bin/pyvenv')
                run('brew unlink python3')
                result = run('brew install python3', warn_only=True)
                if 'Error' in result:
                    abort(result)
            result = run('brew install python3', warn_only=True)
            run('brew link --overwrite python3')
    elif env.target_os == LINUX:
        sudo('add-apt-repository ppa:jonathonf/python-3.6')
        sudo('apt-get update')
        sudo('apt-get install python3.6-dev python3-pip ipython3 python3.6 python3-venv python3.6-venv')
