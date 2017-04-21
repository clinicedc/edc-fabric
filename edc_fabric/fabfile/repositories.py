import os

from io import StringIO

from fabric.api import task, env, cd, run, get, lcd, local
from fabric.contrib.files import exists


def get_repo_name(repo_url=None):
    return repo_url.split('/')[-1:][0].split('.')[0]


@task
def get_repo(repo_url=None, repo_name=None,
             remote_root=None, local_root=None, prompt=None):
    repo_name = repo_name or repo_url.split('/')[-1:][0].split('.')[0]
    local_root = local_root or env.local_source_root
    remote_root = remote_root or env.remote_source_root
    clone_repo(
        repo_url=repo_url,
        remote_root=remote_root,
        prompt=prompt)


@task
def pull_repo(repo_url=None, remote_root=None, branch=None, prompt=None):
    """Pulls a repo on the remote host.
    """
    repo_name = get_repo_name(repo_url)
    with cd(os.path.join(remote_root, repo_name)):
        run('/usr/bin/git checkout {}'.format(branch or 'master'))
        run('/usr/bin/git pull')


@task
def clone_repo(repo_url=None, remote_root=None, branch=None, prompt=None):
    """Clones a repo on the remote host.

    After clone, checkouts branch and pulls
    """
    with cd(remote_root):
        run('/usr/bin/git clone {}'.format(repo_url), warn_only=True)
    pull_repo(repo_url=repo_url, remote_root=remote_root,
              branch=branch, prompt=prompt)


@task
def clone_required_repos_local(local_root=None, project_repo_url=None):
    """Locally Clones all required repos for the project into a local deployment
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


@task
def read_requirements(remote_root=None, project_repo_url=None):
    project_repo_url = project_repo_url or env.project_repo_url
    remote_root = remote_root or env.remote_source_root
    repo_name = get_repo_name(project_repo_url)
    path = os.path.expanduser(os.path.join(
        remote_root, repo_name, 'requirements.txt'))
    fd = StringIO()
    get(path, fd)
    content = fd.getvalue()
    print('content', content)


@task
def clone_required_repos(remote_root=None, project_repo_url=None):
    """Locally Clones all required repos for the project into a local deployment
    folder.
    """
    project_repo_url = project_repo_url or env.project_repo_url
    remote_root = remote_root or env.remote_source_root
    repo_name = get_repo_name(project_repo_url)
    deployment_dir = os.path.join(remote_root, 'deployment', repo_name)
    run('mkdir -p {}'.format(deployment_dir), warn_only=True)
    with cd(deployment_dir):
        repo_dir = os.path.expanduser(os.path.join(deployment_dir, repo_name))
        if not exists(repo_dir):
            run('git clone {}'.format(project_repo_url))
        else:
            with cd(repo_dir):
                run('git pull')
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
