### copy celery templete

    1. sudo cp celeryd.conf /etc/default/celeryd
    2. sudo cp celeryd /etc/init.d/


### config /etc/default/celeryd

    CELERY_BIN="<Celery bin path>"
    CELERYD_CHDIR="<Code directory path>"
    CELERYD_USER="<USER>"
    CELERYD_GROUP="<GROUP>"

### /etc/init.d/celeryd

    $ sudo /etc/init.d/celeryd
    celery init v10.1.
    Using config script: /etc/default/celeryd
    Usage: /etc/init.d/celeryd {start|stop|restart|graceful|kill|dryrun|create-paths}
