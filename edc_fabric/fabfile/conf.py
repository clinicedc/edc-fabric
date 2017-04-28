import os

from fabric.api import env, put, sudo
from fabric.contrib.files import sed, exists
from fabric.utils import abort


def put_project_conf(project_conf=None, map_area=None):
    """Copies the projects <appname>.conf file to remote etc_dir.
    """
    project_conf = project_conf or env.project_conf
    local_copy = os.path.expanduser(os.path.join(
        env.fabric_config_root, 'conf', project_conf))
    remote_copy = os.path.join(env.etc_dir, project_conf)
    if not exists(env.etc_dir):
        sudo('mkdir {etc_dir}'.format(etc_dir=env.etc_dir))
    put(local_copy, remote_copy, use_sudo=True)
    device_id = env.device_id or env.device_ids.get(env.host)
    if not device_id:
        abort('Missing device id. Got None. Check env.')
    sed(remote_copy, 'device_id \=.*',
        'device_id \= {}'.format(device_id), use_sudo=True)
    if not env.device_role:
        abort('Missing device_role. Got None. Check env.')
    sed(remote_copy, 'role \=.*',
        'role \= {}'.format(env.device_role),
        use_sudo=True)
    sed(remote_copy, 'key_path \=.*',
        'key_path \= {}'.format(env.key_path),
        use_sudo=True)
    sed(remote_copy, 'secret_key =.*',
        'secret_key \= {}'.format(env.secret_key),
        use_sudo=True)
    sed(remote_copy, 'crypto_keys_passphrase \=.*',
        'crypto_keys_passphrase \= {}'.format(env.crypto_keys_passphrase),
        use_sudo=True)
