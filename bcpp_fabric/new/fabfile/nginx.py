import os

from fabric.api import sudo, task, put, cd, run
from fabric.contrib.files import exists

NGINX_ROOT = '/etc/nginx/'


@task
def install_nginx():
    run('brew install nginx')


@task
def configure_nginx():

    sites_available_dir = os.path.join(NGINX_ROOT, 'sites-available')
    sites_enabled_dir = os.path.join(NGINX_ROOT, 'sites-enabled')

    if not exists(sites_available_dir):
        sudo('mkdir -p {dir}'.format(dir=sites_available_dir), warn_only=True)
    if not exists(sites_enabled_dir):
        sudo('mkdir -p {dir}'.format(dir=sites_enabled_dir), warn_only=True)
    chmod('755', sites_available_dir, dirr=True)
    put(os.path.join(NGINX_DIR, 'nginx.conf'),
        '/usr/local/etc/nginx/nginx.conf', use_sudo=True)
    put(os.path.join(NGINX_DIR, 'bcpp.conf'),
        '/usr/local/etc/nginx/sites-available/bcpp.conf', use_sudo=True)
    with cd('/usr/local/etc/nginx/sites-enabled'):
        try:
            sudo('ln -s /usr/local/etc/nginx/sites-available/bcpp.conf bcpp.conf')
        except FabricException:
            print(blue('nginx symbolic already created.'))
