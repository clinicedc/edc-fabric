from fabric.api import task


@task
def install_gunicorn():
    with prefix('workon bcpp'):
        run('pip install gunicorn')
    put(os.path.join(GUNICORN_DIR, 'gunicorn.conf.py'),
        '/Users/django/source/bcpp/gunicorn.conf.py', use_sudo=True)
    with cd(PROJECT_DIR):
        run('mkdir -p logs')
        chmod('755', os.path.join(PROJECT_DIR, 'logs'), dirr=True)
        with cd(os.path.join(PROJECT_DIR, 'logs')):
            run('touch gunicorn-access.log')
            run('touch gunicorn-error.log')
    print(green('gunicorn setup completed.'))
