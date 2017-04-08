import os

from fabric.api import cd, env, put, run, sudo, task

env.source_dir = '/Users/django/source'

PROJECT_DIR = os.path.join(env.source_dir, 'bcpp')
GUNICORN_DIR = os.path.join(env.source_dir, 'bcpp-fabric', 'nginx_deployment')


def chmod(permission, file, dirr=False):
    if dirr:
        sudo("chmod -R %s %s" % (permission, file))
    else:
        sudo("chmod %s %s" % (permission, file))


@task
def install_gunicorn():
    put(os.path.join(GUNICORN_DIR, 'gunicorn.conf.py'),
        os.path.join(PROJECT_DIR, 'gunicorn.conf.py'), use_sudo=True)
    with cd(PROJECT_DIR):
        run('mkdir -p logs')
        chmod('755', os.path.join(PROJECT_DIR, 'logs'), dirr=True)
        with cd(os.path.join(PROJECT_DIR, 'logs')):
            run('touch gunicorn-access.log')
            run('touch gunicorn-error.log')
