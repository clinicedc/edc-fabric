# bcpp-fabric

Make a virtualenv 
```
mkvirtualenv -p python3 bcpp-fabric
workon bcpp-fabric
```
Clone fabric repo

```
mkdir -p source ; cd source
git clone git+https://github.com/botswana-harvard/bcpp-fabric.git
```
Install requirements

```
cd bcpp-fabric
pip install -r requirements.txt
```

First time deployment.

1. clone new source project
2. setup nginx 
3. setup gunicorn

```
cd ~/source/bcpp-fabric
vi fabfile.py 
change 'env.update_repo = None' to env.update_repo = False
```

Then specify host to deploy

```
cd ~/source/bcpp-fabric

vi hosts.py
HOSTS = {
    'username@ip:22': 'password',
}

```
Start Deployment

```
cd ~/source/bcpp-fabric
workon bcpp-fabric
fab deploy

```


Update existing project.

1. update existing source project only.

```
change 'env.update_repo = None' to env.update_repo = True
```
Run deployment
```
fab deploy
```
