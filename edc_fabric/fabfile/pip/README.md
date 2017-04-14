
upload/refresh a single package

    pip download -d ~/deployment/bcpp/pip/ gunicorn

upload/refresh a single repo, for example `edc-base`:

    # clear previous version
    rm ~/deployment/bcpp/pip/edc-base*
    
    # copy git url from requirements file used for the deployment 
    pip download -d ~/deployment/bcpp/pip/ git+https://github.com/botswana-harvard/edc-base.git@master#egg=edc_base