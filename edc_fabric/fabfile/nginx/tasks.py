import io
import os
import plistlib

from fabric.api import sudo, task, put, cd, run, env
from fabric.contrib.files import contains, sed
from fabric.context_managers import prefix

from ..environment import update_fabric_env
from ..utils import bootstrap_env
from ..constants import MACOSX, LINUX


@task
def install_nginx_task(**kwargs):
    install_nginx(**kwargs)


def install_nginx(**kwargs):
    if env.target_os == MACOSX:
        install_nginx_macosx(**kwargs)
    elif env.target_os == LINUX:
        install_nginx_linux(**kwargs)


def install_nginx_macosx(bootstrap_path=None, local_fabric_conf=None, bootstrap_branch=None, skip_bootstrap=None):
    if not skip_bootstrap:
        bootstrap_env(
            path=os.path.expanduser(bootstrap_path),
            bootstrap_branch=bootstrap_branch)
        update_fabric_env(use_local_fabric_conf=local_fabric_conf)
    result = run('nginx -V', warn_only=True)
    if env.nginx_version not in result:
        with prefix('export HOMEBREW_NO_AUTO_UPDATE=1'):
            run('brew tap homebrew/services')
            run('brew tap homebrew/nginx')
            result = run(
                'brew install nginx-full --with-upload-module', warn_only=True)
            if 'Error' in result:
                run('brew unlink nginx')
                run('brew install nginx-full --with-upload-module')
    with cd(env.log_root):
        run('touch nginx-error.log')
        run('touch nginx-access.log')
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
            env.static_root, use_sudo=True)
    if contains(remote_server_conf, 'MEDIA_ROOT'):
        sed(remote_server_conf, 'MEDIA_ROOT',
            env.media_root, use_sudo=True)
    create_nginx_plist()


def install_nginx_linux(bootstrap_path=None, local_fabric_conf=None, bootstrap_branch=None, skip_bootstrap=None):
    if not skip_bootstrap:
        bootstrap_env(
            path=os.path.expanduser(bootstrap_path),
            bootstrap_branch=bootstrap_branch)
        update_fabric_env(use_local_fabric_conf=local_fabric_conf)
    result = run('nginx -V', warn_only=True)
    if env.nginx_version not in result:
        sudo('apt-get install nginx curl')
        sudo('ufw allow \'Nginx HTTP\'')
        sudo('systemctl enable nginx')


def create_nginx_plist():
    options = {
        'Label': 'nginx',
        'Program': '/usr/local/bin/nginx',
        'KeepAlive': True,
        'NetworkState': True,
        'RunAtLoad': True,
        'UserName': 'root'}
    plist = plistlib.dumps(options, fmt=plistlib.FMT_XML)
    put(io.BytesIO(plist), '/Library/LaunchDaemons/nginx.plist', use_sudo=True)
    sudo('chown root:wheel /Library/LaunchDaemons/nginx.plist')


@task
def relaunch_web_task():
    relaunch_web()


def relaunch_web():
    sudo('launchctl unload -F /Library/LaunchDaemons/nginx.plist', warn_only=True)
    sudo('nginx -s stop', warn_only=True)
    run('launchctl unload -F /Library/LaunchDaemons/gunicorn.plist', warn_only=True)
    sudo('ps auxww | grep gunicorn | awk \'{print $2}\' | xargs kill -9',
         warn_only=True)
    sudo('launchctl load -F /Library/LaunchDaemons/nginx.plist')
    run('launchctl load -F /Library/LaunchDaemons/gunicorn.plist')
