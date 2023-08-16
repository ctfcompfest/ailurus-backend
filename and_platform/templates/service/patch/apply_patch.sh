#!/usr/bin/env sh

SERVICE_NAME=${1}
PATCH_FILE=${2:-service.patch}
TARGET_DIR=${3:-/}

if [ $# -lt 1 ];
then
    echo "usage: apply_patch.sh <service-name> [<patch-filename> [<target-directory]]"
    exit 1
fi

tar -xv --strip-components=1 -C ${TARGET_DIR} -f ${PATCH_FILE} ${SERVICE_NAME}