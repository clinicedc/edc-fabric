from fabric.api import run, cd
from fabric.contrib.files import sed


def create_new_tag(repo=None):
    """ repo e.g ~/source/edc-sync
    """
    repo = '~/source/edc-rest'
    with cd(repo):
        prev_tag = run('git describe --abbrev=0 --tags')
        prev_tag_line = "version='{}',".format(prev_tag)
        last_tag_digit = prev_tag.split('.')[-1]
        new_tag_digit = int(last_tag_digit) + 1
        new_tag = '{}.{}.{}'.format(
            prev_tag.split('.')[0], prev_tag.split('.')[1], new_tag_digit)
        new_tag_line = "version='{}',".format(new_tag)
    return (prev_tag_line, new_tag_line)


def new_release(repo=None):
    repo = '~/source/edc-rest'
    prev_tag, new_tag = create_new_tag(repo)
    with cd(repo):
        run('git checkout master')
        run('git pull')
        run('git checkout develop')
        run('git pull')
        run('git flow init -d')
        run('git flow release start {}'.format(new_tag))
        sed('setup.py', before=prev_tag, after=new_tag)

        run('git add setup.py')
        run("git commit -m '{}'".format('update code version'))
        run("git flow release finish -m '{}' {}".format(new_tag, new_tag))
        run('git push')
        run('git checkout master')
        run('git push')
        run('git push --tags')
