from fabric.api import env, run, task
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project
from fabric.utils import abort, warn
from fabric.colors import yellow
from fabric.context_managers import prefix


def update_deployment_brew_dir():
    """Rsync's local brew cache to the deployment folder.
    """
    if not exists(env.deployment_brew_dir):
        run('mkdir -p {cache_dir}'.format(
            deployment_brew_dir=env.deployment_brew_dir))
    brew_cache = run('brew --cache')
    rsync_project(local_dir=brew_cache,
                  remote_dir=env.deployment_brew_dir, delete=True)


@task
def update_brew_task(dry_run=None, no_auto_update=None):
    update_brew_cache(dry_run=dry_run, no_auto_update=no_auto_update)


def update_brew_cache(dry_run=None, no_auto_update=None):
    """Rsync's remote brew cache to remote brew cache.

    run:
         brew update && fab -H <host> deploy.update_brew_cache --user=<user>
    so that local brew cache is updated before task starts.
    """
    brew_cache = '~/Library/Caches/Homebrew'
    homebrew = '/usr/local/Homebrew'
    if dry_run:
        if not exists(homebrew):
            warn(yellow('{:}  homebrew folder missing'.format(env.host)))
        else:
            warn('{:}  homebrew folder OK'.format(env.host))
        if not exists(brew_cache):
            warn(yellow('{:} brew_cache folder missing'.format(env.host)))
        else:
            warn('{:} brew_cache folder OK'.format(env.host))
    else:
        rsync_project(local_dir=homebrew + '/',
                      remote_dir=homebrew, delete=True)
        rsync_project(local_dir=brew_cache + '/',
                      remote_dir=brew_cache, delete=True)
        if no_auto_update:
            run('export HOMEBREW_NO_AUTO_UPDATE=1 && brew install wget')
        else:
            result = run('brew update')
            if 'Error' in result:
                if '/usr/local/share/man/man1/brew.1' in result:
                    run('rm -rf /usr/local/share/man/man1/brew.1', warn_only=True)
                if '/usr/local/share/doc/homebrew' in result:
                    run('rm -rf /usr/local/share/doc/homebrew', warn_only=True)
                result = run('brew update')
                if 'Error' in result:
                    abort(result)
            run('brew install wget')
