import configparser
import os

from fabric.api import *

from .constants import LINUX, MACOSX


def update_env(config_path=None):
    config = configparser.RawConfigParser()
    config.read(config_path)
    for key, value in config['default'].items():
        setattr(env, key, value)
        print(key, getattr(env, key))
    for key, value in config['virtualenv'].items():
        setattr(env, key, value)
        print(key, getattr(env, key))
    for key, value in config['repositories'].items():
        if value.lower() in ['true', 'yes']:
            value = True
        elif value.lower() in ['false', 'no']:
            value = False
        setattr(env, key, value)
        print(key, getattr(env, key))
    if env.target_os == LINUX:
        env.python_path = '/usr/bin/'
        env.bash_profile = '~/.bash_aliases'
    elif env.target_os == MACOSX:
        env.python_path = '/usr/local/bin/'
        env.bash_profile = '~/.bash_profiles'
