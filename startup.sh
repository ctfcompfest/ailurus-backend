#!/usr/bin/env sh

# Iterate through each folder in ailurus/svcmodes
for folder in /opt/app/ailurus/svcmodes/*/; do
    # Check if requirements.txt file exists in the current folder
    if [ -f "$folder/requirements.txt" ]; then
        pip3 install -r "$folder/requirements.txt"
    fi
done

CMD=${@:-webapp}
echo $CMD
cd /opt/app && \
    python3 manage.py ${CMD}