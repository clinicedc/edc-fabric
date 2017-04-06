import os

from fabric.api import sudo, task, put, cd, run, env
from fabric.contrib.files import exists, contains, sed

from django.conf import settings as django_settings

from ..environment import update_fabric_env
from ..utils import bootstrap_env


@task
def install_nginx(config_path=None, local_fabric_conf=None, bootstrap_branch=None, skip_bootstrap=None):
    if not skip_bootstrap:
        bootstrap_env(
            path=os.path.expanduser(os.path.join(config_path, 'conf')),
            bootstrap_branch=bootstrap_branch)
        update_fabric_env(use_local_fabric_conf=local_fabric_conf)
    result = run('nginx -V', warn_only=True)
    if env.nginx_version not in result:
        run('brew tap homebrew/services')
        run('brew tap homebrew/nginx')
        run('brew install nginx-full --with-upload-module')
    if not exists('/var/log/nginx'):
        sudo('mkdir -p /var/log/nginx')
    with cd('/var/log/nginx'):
        sudo('touch error.log')
        sudo('touch access.log')
    with cd('/usr/local/etc/nginx'):
        sudo('mv nginx.conf nginx.conf.bak', warn_only=True)
    nginx_conf = os.path.expanduser(os.path.join(
        env.fabric_config_root, 'conf', 'nginx', 'nginx.conf'))
    server_conf = os.path.expanduser(os.path.join(
        env.fabric_config_root, 'conf', 'nginx', env.nginx_server_conf))
    put(nginx_conf, '/usr/local/etc/nginx/', use_sudo=True)
    put(server_conf, '/usr/local/etc/nginx/servers/', use_sudo=True)
    remote_server_conf = os.path.join(
        '/usr/local/etc/nginx/servers/', env.nginx_server_conf)
    if contains(remote_server_conf, 'STATIC_ROOT'):
        sed(remote_server_conf, 'STATIC_ROOT',
            django_settings.STATIC_ROOT, use_sudo=True)
    if contains(remote_server_conf, 'MEDIA_ROOT'):
        sed(remote_server_conf, 'MEDIA_ROOT',
            django_settings.MEDIA_ROOT, use_sudo=True)
