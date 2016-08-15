Клуб АДМ на Хабрахабре и Geektimes
==================================

[![Build Status](https://travis-ci.org/clubadm/clubadm.svg?branch=master)](https://travis-ci.org/clubadm/clubadm)

Данный репозиторий содержит исходные коды сайтов
[Клуба АДМ на Хабрахабре](https://habra-adm.ru/) (кодовое имя `oldsanta`) и
[Клуба АДМ на Geektimes](https://geekadm.ru/) (кодовое имя `newsanta`).

Проект по-прежнему находится в стадии активной разработки. Многое будет доделано
и переделано.

```bash
$ git clone https://github.com/clubadm/faketimes.git
$ cd faketimes
$ python3 faketimes.py
```

```bash
$ git clone https://github.com/clubadm/clubadm.git
$ cd clubadm
$ bower install
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements/dev.txt
$ ./manage.py migrate
$ ./manage.py runserver
$ deactivate
```
