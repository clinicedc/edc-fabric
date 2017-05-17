import os

from fabric.api import cd, run, env, task, get
from fabric.contrib.files import exists

from ..repositories import get_repo_name
from fabric.context_managers import prefix


@task
def pip_download_cache(keep_dir=None):
    """Downloads pip packages into deployment pip dir.
    """
    if not exists(env.deployment_pip_dir):
        #         run('rm -rf {deployment_pip_dir}'.format(
        #             deployment_pip_dir=env.deployment_pip_dir))
        run('mkdir -p {deployment_pip_dir}'.format(
            deployment_pip_dir=env.deployment_pip_dir))
    with cd(env.project_repo_root):
        # can't use
        # run('pip download --python-version 3 --only-binary=:all: '
        # as not all packages have a wheel (arrow, etc)
        pip_download('pip')
        pip_download('setuptools')
        pip_download('ipython')
        pip_download('wheel')
        pip_download('gunicorn')
        run('pip3 download '
            '-d {deployment_pip_dir} -r {requirements}'.format(
                deployment_pip_dir=env.deployment_pip_dir,
                requirements=env.requirements_file), warn_only=True)


def pip_download(package_name):
    """pip downloads a package to the deployment_pip_dir.
    """
    run('pip3 download '
        '-d {deployment_pip_dir} {package_name}'.format(
            deployment_pip_dir=env.deployment_pip_dir,
            package_name=package_name), warn_only=True)


def pip_install_requirements_from_cache(venv_name=None):
    """pip installs required packages from pip_cache_dir into the venv.
    """
    package_names = get_required_package_names()
    for package_name in package_names:
        pip_install_from_cache(package_name=package_name, venv_name=venv_name)


def pip_install_from_cache(package_name=None, pip_cache_dir=None, venv_name=None):
    """pip install a package from pip_cache_dir into the venv.
    """
    pip_cache_dir = pip_cache_dir or env.deployment_pip_dir
    venv_name = venv_name or env.venv_name
    with cd(pip_cache_dir):
        # with prefix('workon {venv_name}'.format(venv_name=venv_name)):
        run('workon {venv_name} && pip3 install --no-cache-dir --no-index --find-links=. {package_name}'.format(
            venv_name=venv_name,
            package_name=package_name))


def get_required_package_names():
    package_names = []
    with cd(env.project_repo_root):
        data = run('cat {requirements}'.format(
            requirements=env.requirements_file))
        data = data.split('\n')
        for line in data:
            if 'botswana-harvard' in line or 'erikvw' in line:
                repo_url = line.split('@')[0].replace('git+', '')
                package_names.append(get_repo_name(repo_url))
    return package_names


def get_pip_list():
    local_path = os.path.expanduser(
        f'~/fabric/download/pip.{env.host}.{env.project_release}.txt')
    if os.path.exists(local_path):
        os.remove(local_path)
    remote_path = f'~/pip.freeze.{env.project_release}.txt'
    run(f'rm {remote_path}', warn_only=True)
    with prefix(f'source {env.venv_dir}/{env.project_appname}/bin/activate'):
        run(f'pip freeze > {remote_path}')
    get(remote_path=remote_path, local_path=local_path)
