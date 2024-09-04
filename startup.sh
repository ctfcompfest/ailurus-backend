#!/usr/bin/env sh

# DB migration
cd /opt/app && python3 manage.py migrate

CMD=${@:-webapp}
echo $CMD
cd /opt/app && python3 manage.py ${CMD}