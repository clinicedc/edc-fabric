# bcpp-fabric

Make a virtualenv 
```
mkvirtualenv -p python3 bcpp-fabric
workon bcpp-fabric
```
Clone fabric repo

```
mkdir -p source ; cd source
git clone https://github.com/botswana-harvard/bcpp-fabric.git
```
Install requirements

```
cd bcpp-fabric
pip install -r requirements.txt
```

First time deployment.

Follow the steps that follow;

```
cd ~/source/bcpp-fabric/bcpp-fabric
vi fabfile.py 
change 'env.update_repo = None' to env.update_repo = False
```

Then specify details of the host to deploy

```
cd ~/source/bcpp-fabric/bcpp-fabric

vi hosts.py
HOSTS = {
    'username@ip:22': 'password',
}

```
Start Deployment

```
cd ~/source/bcpp-fabric/bcpp-fabric
workon bcpp-fabric
fab deploy

```
Update existing project.

1. update existing source project only.

```
cd ~/source/bcpp-fabric/bcpp-fabric
fab update_project
```
Run deployment from scratch
```
cd ~/source/bcpp-fabric/bcpp-fabric
fab deploy

```

Access the system

```
Start server at http://127.0.0.1/
```
