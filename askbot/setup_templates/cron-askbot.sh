#!/usr/bin/env bash
ASKBOT_SITE=${ASKBOT_SITE:-/askbot-site}
export $(cat ${ASKBOT_SITE}/cron_environ | xargs)
cd ${ASKBOT_SITE}
/usr/local/bin/python manage.py send_email_alerts > /proc/1/fd/1 2>/proc/1/fd/2
