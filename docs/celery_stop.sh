#!/bin/sh

cd /var/www/evercloud_web/evercloud_web/
../.venv/bin/celery multi stop evercloud_worker --pidfile=/var/log/evercloud/celery_%n.pid


ps -ef | grep celery
