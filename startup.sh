#!/usr/bin/env sh

CMD=${@:-web}
echo $CMD
cd /opt/app && \
    python3 manage.py ${CMD}