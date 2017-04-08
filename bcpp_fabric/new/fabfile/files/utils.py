from fabric.api import env, sudo


def chmod(permission=None, path=None, recursive=None):
    recursive = False if recursive is None else recursive
    if recursive:
        sudo('chmod -R {permission} {path}'.format(permission, path))
    else:
        sudo('chmod {permission} {path}'.format(permission, path))


def chown(name, recursive=None):
    recursive = False if recursive is None else recursive
    if recursive:
        sudo('chown -R {account}:staff {filename}'.format(
            account=env.account, filename=name))
    else:
        sudo('chown {account}:staff {filename}'.format(
            account=env.account, filename=name))
