from fabric.api import *
from fabric.contrib.project import rsync_project


env.user = 'root'
env.hosts = ['habra-adm.ru']
env.use_ssh_config = True


def pack():
    local('python3 setup.py sdist --formats=gztar', capture=False)


def deploy():
    dist = local('python3 setup.py --fullname', capture=True).strip()
    put('dist/%s.tar.gz' % dist, '/tmp/clubadm.tar.gz')
    run('tar xzf /tmp/clubadm.tar.gz -C /tmp')
    with cd('/tmp/%s' % dist):
        run('python3 setup.py install')
    run('rm -rf /tmp/clubadm /tmp/clubadm.tar.gz')
    with shell_env(DJANGO_SETTINGS_MODULE='oldsanta.settings'):
        local('python3 manage.py collectstatic --noinput')
        rsync_project(local_dir='oldsanta-static/',
                      remote_dir='/var/www/oldsanta/static')
    with shell_env(DJANGO_SETTINGS_MODULE='kafenet.oldsanta.settings'):
         run('django-admin migrate')
    put('oldsanta/uwsgi.ini', '/etc/uwsgi/oldsanta.ini')
    run('uwsgi --reload /var/run/oldsanta.pid')
    with shell_env(DJANGO_SETTINGS_MODULE='newsanta.settings'):
        local('python3 manage.py collectstatic --noinput')
        rsync_project(local_dir='newsanta-static/',
                      remote_dir='/var/www/newsanta/static')
    with shell_env(DJANGO_SETTINGS_MODULE='kafenet.newsanta.settings'):
         run('django-admin migrate')
    put('newsanta/uwsgi.ini', '/etc/uwsgi/newsanta.ini')
    run('uwsgi --reload /var/run/newsanta.pid')
    put('nginx.conf', '/etc/nginx/sites-enabled/clubadm.conf')
    run('service nginx restart')
    run('service celeryd restart')
