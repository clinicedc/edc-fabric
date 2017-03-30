import os

from fabric.api import *
from fabric.contrib.project import rsync_project
from fabric.contrib.files import exists


def get_repo_name(repo_url=None):
    return repo_url.split('/')[-1:][0].split('.')[0]


@task
def get_repo(repo_url=None, repo_name=None, use_rsync=None,
             remote_root=None, local_root=None, prompt=None):
    repo_name = repo_name or repo_url.split('/')[-1:][0].split('.')[0]
    local_root = local_root or env.local_source_root
    remote_root = remote_root or env.remote_source_root
    if use_rsync:
        rsync_repo(repo_name=repo_name,
                   local_root=local_root,
                   remote_root=remote_root,
                   prompt=prompt)
    else:
        clone_repo(
            repo_url=repo_url,
            remote_root=remote_root,
            prompt=prompt)


@task
def clone_repo(repo_url=None, remote_root=None, branch=None, prompt=None):
    """Clones a repo on the remote host.
    """
    with cd(remote_root):
        run('/usr/bin/git clone {}'.format(repo_url), warn_only=True)
    repo_name = get_repo_name(repo_url)
    with cd(os.path.join(remote_root, repo_name)):
        run('/usr/bin/git checkout {}'.format(branch or 'master'))
        run('/usr/bin/git pull')


@task
def rsync_repo(repo_name=None, local_root=None, remote_root=None, branch=None, prompt=None):
    """Rsyncs a local repo to the remote host.
    """
    with lcd(os.path.join(local_root, repo_name)):
        local('/usr/bin/git checkout {}'.format(branch or 'master'))
        local('/usr/bin/git pull')
        rsync_project(local_dir=os.path.join(local_root, repo_name),
                      remote_dir=os.path.join(remote_root, repo_name),
                      exclude=['.git'])
        local('/usr/bin/git checkout develop')


@task
def clone_required_repos(local_root=None, project_repo_url=None):
    """Clones all required repos for the project into a local deployment
    folder.
    """
    project_repo_url = project_repo_url or env.project_repo_url
    local_root = local_root or env.local_source_root
    repo_name = get_repo_name(project_repo_url)
    deployment_dir = os.path.join(local_root, 'deployment', repo_name)
    local('mkdir -p {}'.format(deployment_dir))
    with lcd(deployment_dir):
        repo_dir = os.path.expanduser(os.path.join(deployment_dir, repo_name))
        if not os.path.exists(repo_dir):
            local('git clone {}'.format(project_repo_url))
        else:
            with lcd(repo_dir):
                local('git pull')
        with open(os.path.expanduser(os.path.join(deployment_dir, repo_name, 'requirements.txt')), 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'botswana-harvard' in line or 'erikvw' in line:
                    repo_url = line.split('@')[0].replace('git+', '')
                    repo_name = get_repo_name(repo_url)
                    repo_dir = os.path.expanduser(
                        os.path.join(deployment_dir, repo_name))
                    if not os.path.exists(repo_dir):
                        local('git clone {}'.format(
                            line.split('@')[0].replace('git+', '')))
                    else:
                        with lcd(repo_dir):
                            local('git pull')

    # local('tar -czvf all_repos.tar.gz -C {} .'.format(repo_dir))
