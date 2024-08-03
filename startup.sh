#!/usr/bin/env sh

CMD=${@:-webapp}
echo $CMD
cd /opt/app && \
    python3 manage.py ${CMD}