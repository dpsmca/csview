#!/usr/bin/env bash

CALL_DIR="${PWD}"
MYNAME="${0}"
MYPATH="$(realpath ${MYNAME})"
BASE_DIR="$(dirname ${MYPATH})"
VENV_HOME="${MYPATH}/venv"
VENV_SCRIPT="${VENV_HOME}/bin/activate"
DEPS_FILE="requirements.txt"
DEPS_PATH="${BASE_DIR}/${DEPS_FILE}"

if [[ -d "${BASE_DIR}" && ! -e "${VENV_SCRIPT}" && -e "${DEPS_PATH}" ]]; then
  cd "${BASE_DIR}"
  pip install -r "${DEPS_FILE}"
  python3 -m venv venv
fi

if [[ ! -e "${VENV_SCRIPT}" ]]; then
  printf "ERROR: Could not find or create Python virtual environment at: '%s'\n" "${VENV_HOME}"
  exit 1
fi

source "${VENV_SCRIPT}"

python3 csview.py "${@}"
