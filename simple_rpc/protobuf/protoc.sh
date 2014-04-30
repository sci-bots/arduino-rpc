#!/bin/bash
#set -x
NARGS=$#

function main {
    if [ $NARGS -lt 3 ]; then
        usage
    fi
}

function usage {
    echo "Usage: $0 <nanopb home> <protobuf definition> <outdir>"
    exit 1
}

main

NANOPB_HOME=$1
PROTOBUF_DEFINITION=$2
OUTPUT_DIR=$3
PYTHON_OUT_DIR=${OUTPUT_DIR}/py
NANO_OUT_DIR=${OUTPUT_DIR}/nano

mkdir -p ${PYTHON_OUT_DIR}
mkdir -p ${NANO_OUT_DIR}

protoc --plugin=protoc-gen-nanopb=${NANOPB_HOME}/generator/protoc-gen-nanopb \
    ${PROTOBUF_DEFINITION} --nanopb_out=${NANO_OUT_DIR} \
    --python_out=${PYTHON_OUT_DIR}
