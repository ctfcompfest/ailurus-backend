#!/usr/bin/env sh

flask db upgrade

CMD=${@:-web}
echo $CMD
cd /opt/app && \
    python3 manage.py ${CMD}