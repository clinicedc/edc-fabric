import os

from fabric.api import cd, run, env, prefix, task
from fabric.contrib.files import exists

from ..env import update_fabric_env
from ..repositories import get_repo_name
from ..utils import bootstrap_env


@task
def pip_download_core(bootstrap_path=None, local_fabric_conf=None, bootstrap_branch=None):
    bootstrap_env(
        path=os.path.expanduser(bootstrap_path),
        bootstrap_branch=bootstrap_branch)
    update_fabric_env(use_local_fabric_conf=local_fabric_conf)
    pip_download('pip')
    pip_download('setuptools')
    pip_download('ipython')
    pip_download('pillow')
    pip_download('pillow==2.4.0')
    pip_download('paramiko')
    pip_download('cryptography')
    pip_download('cryptography==1.1')
    pip_download('simplejson')


def pip_download_cache():
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


def pip_install_requirements_from_cache():
    """pip installs required packages from pip_cache_dir into the venv.
    """
    package_names = get_required_package_names()
    for package_name in package_names:
        pip_install_from_cache(package_name)


def pip_install_from_cache(package_name, pip_cache_dir=None):
    """pip install a package from pip_cache_dir into the venv.
    """
    pip_cache_dir = pip_cache_dir or env.deployment_pip_dir
    with cd(pip_cache_dir):
        with prefix('source {}'.format(os.path.join(env.venv_dir, env.venv_name, 'bin', 'activate'))):
            run('pip install --no-index --find-links=. {package_name}'.format(
                package_name=package_name), warn_only=True)


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
