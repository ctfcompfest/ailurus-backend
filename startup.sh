#!/usr/bin/env sh

flask --app "and_platform:create_app()" db upgrade

CMD=${@:-web}
echo $CMD
cd /opt/app && \
    python3 manage.py ${CMD}