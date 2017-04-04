from fabric.api import sudo, task, env

from .constants import LINUX, MACOSX


@task
def disable_apache(target_os=None, prompt=None):
    target_os = target_os or env.target_os
    if target_os == LINUX:
        sudo('systemctl stop apache2.service', warn_only=True)
        sudo('systemctl disable apache2', warn_only=True)
    elif target_os == MACOSX:
        sudo('launchctl unload -w /System/Library/LaunchDaemons/org.apache.httpd.plist', warn_only=True)
    else:
        raise Exception('Unknown OS/System. Got \'{}\''.format(target_os))
