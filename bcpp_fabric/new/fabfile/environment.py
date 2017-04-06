import configparser
import os

from fabric.api import env, run, local
from fabric.contrib.files import exists
from fabric.utils import abort

from .constants import LINUX, MACOSX


def update_fabric_env(use_local_fabric_conf=None):
    config = configparser.RawConfigParser()
    user = env.user
    if use_local_fabric_conf:
        data = local('cat {path}'.format(
            path=os.path.expanduser(env.fabric_config_path)), capture=True)
    else:
        if not exists(env.fabric_config_path):
            abort('Missing config file. Expected {path}'.format(
                path=env.fabric_config_path))
        data = run('cat {path}'.format(path=env.fabric_config_path))
    config.read_string(data)
    for key, value in config['default'].items():
        setattr(env, key, value)
        print(key, getattr(env, key))
    for key, value in config['python'].items():
        setattr(env, key, value)
        print(key, getattr(env, key))
    for key, value in config['nginx'].items():
        setattr(env, key, value)
        print(key, getattr(env, key))
    for key, value in config['mysql'].items():
        setattr(env, key, value)
        print(key, getattr(env, key))
    for key, value in config['venv'].items():
        setattr(env, key, value)
        print(key, getattr(env, key))
    for key, value in config['repositories'].items():
        if value.lower() in ['true', 'yes']:
            value = True
        elif value.lower() in ['false', 'no']:
            value = False
        setattr(env, key, value)
        print(key, getattr(env, key))
    for key, value in config['gpg'].items():
        setattr(env, key, value)
        print(key, getattr(env, key))
    for key, value in config['crypto_fields'].items():
        setattr(env, key, value)
        print(key, getattr(env, key))
    # env.dmg_passphrases = config.get('dmg_passphrases', {})
    if env.target_os == LINUX:
        env.python_path = '/usr/bin/'
        env.bash_profile = '~/.bash_aliases'
    elif env.target_os == MACOSX:
        env.python_path = '/usr/local/bin/'
        env.bash_profile = '~/.bash_profile'
        env.dmg_path = env.dmg_path or os.path.join(env.etc_dir)
        print('dmg_path (updated)', env.dmg_path)
    env.create_env = True
    env.update_requirements = True
    env.update_collectstatic = True
    env.update_collectstatic_js_reverse = True
    if user:
        env.user = user


# def update_fabric_env_hosts(config_path=None):
#     config = configparser.RawConfigParser()
#     config_path = config_path or '~/deployment/secrets.conf'
#     config_path = os.path.expanduser(os.path.join(config_path, 'hosts.conf')
#     print('Reading hosts from ', config_path)
#     config.read(config_path)
#     for host, pwd in config['hosts'].items():
#         if '@' not in host:
#             host = '{}@{}'.format(env.user, host)
#         env.passwords.update({'{}:22'.format(host): pwd})
#         env.hosts.append(host)
#     print('hosts', env.hosts)
#     print('passwords', env.passwords)


def update_fabric_env_device_ids(config_path=None):
    """Reads config from device_ids.conf.

    Format: hostname = device_role,device_id
    Example: myhostname = Client,55
    """
    config = configparser.RawConfigParser()
    config_path = config_path or '~/deployment/device_ids.conf'
    config_path = os.path.expanduser(config_path)
    print('Reading device_ids from ', config_path)
    config.read(config_path)
    env.device_ids = {}
    env.device_roles = {}
    for host, device in config['edc_device'].items():
        device_role, device_id = device.split(',')
        env.device_ids.update({host: device_id})
        env.device_roles.update({host: device_role})
    print('device_ids', env.device_ids)


def update_fabric_env_key_volumes(config_path=None):
    config = configparser.RawConfigParser()
    config_path = config_path or '~/deployment/secrets.conf'
    config_path = os.path.expanduser(config_path)
    print('Reading key_volumes from ', config_path)
    config.read(config_path)
    env.key_volume_password = config['key_volumes'].get('key_volume_password')
#     env.key_volumes = {}
#     for host, pwd in config['key_volumes'].items():
#         env.key_volumes.update({host: pwd})
#     print('key_volumes', env.key_volumes)
