import os
import random

from datetime import datetime

from fabric.api import cd, env, get, local, prompt, put, run, sudo

from fabric.contrib.console import confirm
from fabric.contrib.files import append, comment, contains, exists, \
    uncomment, upload_template


env.colorize_errors = True
env.use_ssh_config = True


def test():
    """Протестировать бизнес-логику."""
    local('source venv/bin/activate && python3 manage.py '
          'test clubadm --settings oldsanta.settings', shell='/bin/bash')
    local('source venv/bin/activate && python3 manage.py '
          'test clubadm --settings newsanta.settings', shell='/bin/bash')


def setup_user():
    """Создать нового системного пользователя."""
    if not exists('/home/apps/clubadm'):
        run('mkdir -p /home/apps')
        run('adduser --system --home /home/apps/clubadm --group clubadm')
        run('chmod 740 /home/apps/clubadm')


def setup_virtualenv():
    """Установить Virtualenv и создать новое виртуальное окружение."""
    if not exists('/usr/bin/pip3'):
        run('apt-get -qqy install python3-pip > /dev/null')
    if not exists('/usr/local/bin/virtualenv'):
        run('pip3 install -Uq virtualenv > /dev/null')
    if not exists('/home/apps/clubadm/venv'):
        sudo('virtualenv -p python3 /home/apps/clubadm/venv > /dev/null',
             user='clubadm')


def upload():
    """Загрузить мастер-ветку на сервер и установить Python-зависимости."""
    local('git archive --format=tar master | gzip > clubadm.tar.gz')
    put('clubadm.tar.gz', '/home/apps/clubadm/clubadm.tar.gz')
    with cd('/home/apps/clubadm'):
        sudo('tar zxf clubadm.tar.gz', user='clubadm')
        sudo('source venv/bin/activate && '
             'pip install -Uq -r requirements/prod.txt > /dev/null')
        run('rm clubadm.tar.gz')
    local('rm clubadm.tar.gz')


def setup_rabbitmq():
    """Установить и настроить RabbitMQ.

    После установки создает два новых виртуальных хоста (для Хабрахабра и
    Geektimes).
    """
    if not exists('/usr/sbin/rabbitmq-server'):
        run('apt-get -qqy install rabbitmq-server > /dev/null')
        run('service rabbitmq-server start')
    hosts = run('rabbitmqctl list_vhosts')
    if 'oldsanta' not in hosts:
        run('rabbitmqctl add_vhost oldsanta')
        run('rabbitmqctl set_permissions -p oldsanta guest ".*" ".*" ".*"')
    if 'newsanta' not in hosts:
        run('rabbitmqctl add_vhost newsanta')
        run('rabbitmqctl set_permissions -p newsanta guest ".*" ".*" ".*"')


def setup_memcached():
    """Установить memcached.

    Дедушка Мороз очень любит раритет.
    """
    if not exists('/usr/bin/memcached'):
        run('apt-get -qqy install memcached > /dev/null')
        run('service memcached start')
    if not exists('/usr/include/libmemcached'):
        run('apt-get -qqy install libmemcached-dev > /dev/null')


def setup_postgresql():
    """Установить и настроить PostgreSQL.

    После установки добавляет нового пользователя clubadm (peer-аутентификация)
    и создает две базы данных (для Хабрахабра и Geektimes). Если в локальной
    директории backups есть какие-то дампы, то будет предложено загрузить
    последний из них.
    """
    if not exists('/usr/bin/psql'):
        run('apt-get -qqy install postgresql > /dev/null')
        run('service postgresql start')
    if not exists('/usr/include/postgresql'):
        run('apt-get -qqy install libpq-dev > /dev/null')
    postgres = sudo('psql --list', user='postgres')
    if 'clubadm' not in postgres:
        sudo('createuser clubadm', user='postgres')
    for project in ['oldsanta', 'newsanta']:
        if project in postgres:
            continue
        sudo('createdb --owner=clubadm %s' % project, user='postgres')
        backup = None
        for dirpath, dirnames, filenames in os.walk('backups'):
            for filename in filenames:
                if project in filename and (
                        backup is None or filename > backup):
                    backup = filename
        if backup and confirm('База пуста. Накатить %s?' % backup):
            backup = os.path.join(dirpath, backup)
            put(backup, '/tmp/backup.sql', mode='544')
            sudo('psql %s < /tmp/backup.sql' % project, user='postgres')
            run('rm /tmp/backup.sql')


def setup_uwsgi():
    """Установить и настроить uWSGI."""
    if not exists('/usr/local/bin/uwsgi'):
        run('apt-get -qqy install uwsgi-core uwsgi-plugin-python3 > /dev/null')
    if not exists('/var/log/uwsgi'):
        run('mkdir -p /var/log/uwsgi')
        run('chown clubadm:clubadm /var/log/uwsgi')
        run('chmod 750 /var/log/uwsgi')
    if not exists('/var/run/uwsgi'):
        run('mkdir -p /var/run/uwsgi')
    if not contains('/etc/rc.local', 'clubadm'):
        comment('/etc/rc.local', 'exit 0')
        append('/etc/rc.local', [
            'uwsgi_python35 --ini /home/apps/clubadm/oldsanta/uwsgi.ini',
            'uwsgi_python35 --ini /home/apps/clubadm/newsanta/uwsgi.ini',
            'exit 0'
        ])
        run('/etc/rc.local')


def setup_openssl():
    """Настроить OpenSSL."""
    if not exists('/etc/ssl/dhparam.pem'):
        run('openssl dhparam -out /etc/ssl/dhparam.pem 2048 > /dev/null')


def setup_letsencrypt():
    """Установить и настроить Letsencrypt."""
    if not exists('/opt/certbot'):
        run('apt-get -qqy install git > /dev/null')
        run('git clone -q https://github.com/certbot/certbot.git /opt/certbot')
    if not exists('/etc/letsencrypt/live/habra-adm.ru'):
        run('/opt/certbot/certbot-auto certonly --webroot --agree-tos -nq '
            '-m kafemanw@gmail.com -w /var/www/oldsanta '
            '-d habra-adm.ru -d www.habra-adm.ru')
    if not exists('/etc/letsencrypt/live/geekadm.ru'):
        run('/opt/certbot/certbot-auto certonly --webroot --agree-tos -nq '
            '-m kafemanw@gmail.com -w /var/www/newsanta '
            '-d geekadm.ru -d www.geekadm.ru')
    if not exists('/var/log/letsencrypt'):
        run('mkdir -p /var/log/letsencrypt')
        run('chmod 750 /var/log/letsencrypt')
    if not exists('/etc/cron.monthly/letsencrypt'):
        append('/etc/cron.monthly/letsencrypt', [
            '#!/bin/sh',
            '/opt/certbot/certbot-auto renew >> /var/log/letsencrypt/renew.log',
            'service nginx reload',
        ])
        run('chmod 751 /etc/cron.monthly/letsencrypt')


def setup_nginx():
    """Установить и настроить nginx."""
    if not exists('/usr/sbin/nginx'):
        run('apt-get -qqy install nginx-full')
    with cd('/var/www'):
        if not exists('oldsanta'):
            run('mkdir oldsanta')
            run('chown clubadm:clubadm oldsanta')
            run('chmod 755 oldsanta')
        if not exists('newsanta'):
            run('mkdir newsanta')
            run('chown clubadm:clubadm newsanta')
            run('chmod 755 newsanta')
    with cd('/etc/nginx'):
        uncomment('nginx.conf', 'server_tokens off')
        uncomment('nginx.conf', 'gzip_types')
    run('ln -sf /home/apps/clubadm/oldsanta/nginx.conf '
        '/etc/nginx/sites-enabled/oldsanta.conf')
    run('ln -sf /home/apps/clubadm/newsanta/nginx.conf '
        '/etc/nginx/sites-enabled/newsanta.conf')


def setup_local_settings():
    """Обновить локальные настройки для наших django-проектов.

    Если такие настройки уже существуют (например, команда вызывается не в
    первый раз), то необходимо подтвердить перезапись (отдельно для каждого
    проекта).
    """
    for project in ['oldsanta', 'newsanta']:
        settings = '/home/apps/clubadm/%s/local_settings.py' % project
        if exists(settings) and not confirm('Обновить %s?' % settings):
            continue
        secret_key = ''.join([random.SystemRandom().choice(
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/?!='
        ) for i in range(100)])
        tmauth_client = prompt('Введите TMAUTH_CLIENT для %s:' % project)
        tmauth_secret = prompt('Введите TMAUTH_SECRET для %s:' % project)
        upload_template('%s/local_settings.py.example' % project, settings, {
            'secret_key': secret_key,
            'tmauth_client': tmauth_client,
            'tmauth_secret': tmauth_secret
        }, use_jinja=True, backup=False, mode='400')
        run('chown clubadm:clubadm %s' % settings)
    if not exists('/var/log/clubadm'):
        run('mkdir /var/log/clubadm')
        run('chown clubadm:clubadm /var/log/clubadm')
        run('chmod 700 /var/log/clubadm')


def collectstatic():
    """Скомпилировать всю статику и собрать в одном месте."""
    if not exists('/usr/bin/node'):
        run('apt-get -qqy install nodejs-legacy > /dev/null')
    if not exists('/usr/bin/npm'):
        run('apt-get -qqy install npm > /dev/null')
    if not exists('/usr/bin/lessc'):
        run('apt-get -qqy install node-less > /dev/null')
    if not exists('/usr/local/bin/bower'):
        run('npm install -gs bower')
    if not exists('/usr/local/bin/yuglify'):
        run('npm install -gs yuglify')
    with cd('/home/apps/clubadm'):
        sudo('HOME=/home/apps/clubadm bower install', user='clubadm')
        sudo('source venv/bin/activate && python manage.py collectstatic -v 0 '
             '--settings oldsanta.settings --noinput', user='clubadm')
        sudo('source venv/bin/activate && python manage.py collectstatic -v 0 '
             '--settings newsanta.settings --noinput', user='clubadm')


def migrate():
    """Обновить структуру таблиц базы данных."""
    with cd('/home/apps/clubadm'):
        sudo('source venv/bin/activate && python manage.py '
             'migrate -v 0 --settings oldsanta.settings', user='clubadm')
        sudo('source venv/bin/activate && python manage.py '
             'migrate -v 0 --settings newsanta.settings', user='clubadm')


def reload_uwsgi():
    """Перезапустить uwsgi (= наши django-проекты)."""
    run('uwsgi_python35 --reload /var/run/uwsgi/oldsanta.pid')
    run('uwsgi_python35 --reload /var/run/uwsgi/newsanta.pid')


def reload_nginx():
    """Перезапустить Nginx."""
    run('service nginx reload')


def backup():
    """Создать резервную копию базы данных и загрузить ее на локальный хост."""
    filename = datetime.now().strftime('backups/%Y/%m/%%s-%Y%m%d%H%M%S.sql')
    for project in ['oldsanta', 'newsanta']:
        sudo('pg_dump %s > /tmp/dump.sql' % project, user='postgres')
        get('/tmp/dump.sql', filename % project)
        run('rm /tmp/dump.sql')


def deploy():
    """Выполнить полное развертывание приложения, включая настройку сервера."""
    test()
    setup_user()
    setup_virtualenv()
    setup_memcached()
    setup_postgresql()
    upload()
    setup_rabbitmq()
    setup_uwsgi()
    setup_openssl()
    setup_letsencrypt()
    setup_nginx()
    setup_local_settings()
    collectstatic()
    migrate()
    reload_uwsgi()
    reload_nginx()
