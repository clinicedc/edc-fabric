# bcpp-fabric

## Install `Fabric3` and `bcpp_fabric` in a virtualenv

Make a new clean virtualenv

    mkdir ~/.venv
    cd ~/.venv
    python3 -m venv bcpp-fabric
    source ~/.venv/bin/activate

Update pip in your new virtualenv

    pip install -U pip ipython

Install `Fabric3` in your new virtualenv

    pip install Fabric3

Clone `bcpp-fabric`, lets clone this in `~/source`

    cd ~/source && git clone https://github.com/botswana-harvard/bcpp-fabric.git

Run the `prepare_local_for_deploy` task

    cd ~/source/bcpp-fabric/bcpp_fabric/new
    fab prepare_local_for_deploy


### First time deployment with `fabric`.

Follow the steps that follow;

```bash
cd ~/source/bcpp-fabric/bcpp-fabric
vi fabfile.py 
change 'env.update_repo = None' to env.update_repo = False
```

Then specify details of the host to deploy

```bash
cd ~/source/bcpp-fabric/bcpp-fabric

vi hosts.py
HOSTS = {
    'username@ip:22': 'password',
}

```
create and or edit bcpp.conf file

```bash
nano /etc/bcpp.conf

```

Start Deployment

```bash
cd ~/source/bcpp-fabric/bcpp-fabric
workon bcpp-fabric
fab deploy:mysqlpwd=<pass>,

```
### Update existing project.

update existing source project only.

```bash
cd ~/source/bcpp-fabric/bcpp-fabric
fab update_project
```
Run deployment from scratch

```bash
cd ~/source/bcpp-fabric/bcpp-fabric
fab deploy
```
Access the system

Start server at http://127.0.0.1/


### Installation of repos

The following tasks contribute:
* `fab -P deploy`  - To make a first time deployment, run this command.
* `fab -P clone_packages` - Run this task if the repos existing are outdated.
* `fab -P install_all_repos` - If the local repos are up-to-date, run this task

Note:
`fab -P <task>` to run deployement in parallel, all machines at once.
`fab -P -z <number_of_hosts> <task>` to deploy certain number of machines
