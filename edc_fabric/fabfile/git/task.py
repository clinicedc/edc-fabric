import os

from fabric.api import local, lcd, env, warn, task, abort, settings
from fabric.colors import blue

from ..repositories import get_repo_name


@task
def cut_releases(source_root=None, project_repo_name=None, requirements_file=None, dry_run=None):
    """
    Cuts releases on the local machine.
    """
    source_root = source_root or env.source_root
    project_repo_name = project_repo_name or env.project_repo_name
    requirements_file = requirements_file or env.requirements_file
    # release project repo.
    new_release(source_root=source_root,
                repo_name=project_repo_name, dry_run=dry_run)
    # release requirements
    with open(os.path.join(source_root, project_repo_name, requirements_file), 'r') as f:
        lines = f.read()
        for line in lines.split('\n'):
            if 'botswana-harvard' in line or 'erikvw' in line:
                repo_url = line.split('@')[0].replace('git+', '')
                repo_name = get_repo_name(repo_url)
                if repo_name:
                    new_release(source_root=source_root,
                                repo_name=repo_name, dry_run=dry_run)


def get_next_tag(current_tag=None):
    """
    Returns the next tag.
    """
    tag = current_tag.split('.')
    minor_version = int(tag[-1:][0]) + 1
    tag = tag[:-1]
    tag.append(str(minor_version))
    return '.'.join(tag)


@task
def new_release(source_root=None, repo_name=None, dry_run=None, git_flow_init=None):
    """Cuts a release for the given repo.

    Tag is incremented as a patch, e.g. 0.1.11 -> 0.1.12

    Example:

        fab -H localhost common.new_release:source_root=/Users/erikvw/source,repo_name=bcpp-subject

    """
    source_root = source_root or env.remote_source_root
    with lcd(os.path.join(source_root, repo_name)):
        print(os.path.join(source_root, repo_name))
        local('git checkout master')
        local('git pull')
        if git_flow_init:
            local('git flow init -d')
        local('git checkout develop')
        local('git pull')
        with settings(warn_only=True):
            current_tag = local('git describe --abbrev=0 --tags', capture=True)
        if 'fatal' in current_tag or not current_tag:
            current_tag = '0.1.0'
        next_tag = get_next_tag(current_tag)
        result = local('git diff --name-status master..develop', capture=True)
        if not result:
            warn(blue('{repo_name}: release {current_tag} is current'.format(
                repo_name=repo_name,
                current_tag=current_tag)))
        else:
            if dry_run:
                print('{repo_name}-{current_tag}: git flow release start '
                      '{next_tag}'.format(
                          repo_name=repo_name,
                          current_tag=current_tag,
                          next_tag=next_tag))
            else:

                version_string_before = 'version=\'{current_tag}\''.format(
                    current_tag=current_tag)
                version_string_after = 'version=\'{next_tag}\''.format(
                    next_tag=next_tag)
                path = os.path.expanduser(
                    os.path.join(source_root, repo_name, 'setup.py'))
                if not os.path.exists(path):
                    abort('{repo_name}: setup.py does not exist. Got {path}'.format(
                        repo_name=repo_name, path=path))
                data = local('cat setup.py', capture=True)
                if version_string_before not in data:
                    abort('{repo_name}: {version_string_before} not found '
                          'in setup.py'.format(
                              repo_name=repo_name,
                              version_string_before=version_string_before,
                              current_tag=current_tag))
                local('git flow release start {}'.format(next_tag))
                data = local('cat setup.py', capture=True)
                data = data.replace(version_string_before,
                                    version_string_after)
                local('echo "{data}" > setup.py'.format(data=data))
                local('git add setup.py')
                local('git commit -m \'bump version\'')
                local("git flow release finish {}".format(next_tag))
                local('git push')
                local('git push --tags')
                local('git checkout master')
                local('git push')
                local('git checkout develop')
