import os

from fabric.api import task, env, put, sudo
from fabric.contrib.files import sed, exists


@task
def put_project_conf(config_filename=None):
    """Copies the projects <appname>.conf file to remote etc_dir
    and updates required attrs.

    Expects a deployment copy to be in the deploymeny folder.
    """
    config_filename = config_filename or '{appname}.conf'.format(
        appname=env.project_appname)
    local_copy = os.path.join(os.path.expanduser(
        env.deployment_root), config_filename)
    remote_copy = os.path.join(env.etc_dir, config_filename)
    if not exists(env.etc_dir):
        sudo('mkdir {etc_dir}'.format(etc_dir=env.etc_dir))
    put(local_copy, remote_copy, use_sudo=True)
    sed(remote_copy, 'device_id \=.*',
        'device_id \= {}'.format(env.device_ids.get(env.host)),
        use_sudo=True)
    sed(remote_copy, 'role \=.*',
        'role \= {}'.format(env.device_roles.get(env.host)),
        use_sudo=True)
    sed(remote_copy, 'key_path \=.*',
        'key_path \= {}'.format(env.key_path),
        use_sudo=True)
