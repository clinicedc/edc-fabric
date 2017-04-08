from fabric.api import env, run
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project
from fabric.utils import abort


def update_deployment_brew_dir():
    """Rsync's local brew cache to the deployment folder.
    """
    if not exists(env.deployment_brew_dir):
        run('mkdir -p {cache_dir}'.format(
            deployment_brew_dir=env.deployment_brew_dir))
    brew_cache = run('brew --cache')
    rsync_project(local_dir=brew_cache,
                  remote_dir=env.deployment_brew_dir, delete=True)


def update_brew_cache():
    """Rsync's remote brew deployment folder to remote brew cache.
    """
    result = run('brew update')
    if 'Error' in result:
        if '/usr/local/share/man/man1/brew.1' in result:
            run('rm -rf /usr/local/share/man/man1/brew.1', warn_only=True)
        if '/usr/local/share/doc/homebrew' in result:
            run('rm -rf /usr/local/share/doc/homebrew', warn_only=True)
        result = run('brew update')
        if 'Error' in result:
            abort(result)
    brew_cache = run('brew --cache')
    run('rsync -pthrvz --delete {deployment_brew_dir} {brew_cache}'.format(
        deployment_brew_dir=env.deployment_brew_dir,
        brew_cache=brew_cache))
