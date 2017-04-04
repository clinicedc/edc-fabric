from fabric.api import cd, task, env, run, settings

from fabric.colors import red


@task
def dismount_dmg(volume_name=None):
    """Dismounts a dmg file on the remote host.
    """
    with cd(volume_name):
        with settings(warn_only=True):
            result = run('diskutil unmount {}'.format(volume_name))
            if result.failed:
                print(red('{host} Dismount failed for {volume_name}'.format(
                    host=env.host, volume_name=volume_name)))


@task
def mount_dmg(dmg_path=None, dmg_filename=None):
    """Mounts a dmg file on the remote host.
    """
    dmg_path = dmg_path or env.dmg_path
    dmg_filename = dmg_filename or env.dmg_filename
    with cd(dmg_path):
        result = run('hdiutil attach -stdinpass {}'.format(dmg_filename))
        if result.failed:
            print(red('{host} Mount failed for {dmg_filename}'.format(
                host=env.host, dmg_filename=dmg_filename)))
