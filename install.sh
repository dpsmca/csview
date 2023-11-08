#!/usr/bin/env bash
TERM="xterm-256color"

PROGRAM_NAME="csview"
CALL_DIR="${PWD}"
MYNAME="${0}"
PYTHON3="$(command -v python3)"
MYPATH="$(realpath ${MYNAME})"
BASE_DIR="$(dirname ${MYPATH})"
VENV_HOME="${BASE_DIR}/venv"
VENV_SCRIPT="${VENV_HOME}/bin/activate"
DEPS_FILE="requirements.txt"
DEPS_PATH="${BASE_DIR}/${DEPS_FILE}"
WRAPPER_NAME="${PROGRAM_NAME}.sh"
SCRIPT_NAME="${PROGRAM_NAME}.py"
WRAPPER="${BASE_DIR}/${WRAPPER_NAME}"
SCRIPT="${BASE_DIR}/${SCRIPT_NAME}"

TPUT="tput -T${TERM}"
BOLD="$(${TPUT} bold)"
UL="$(${TPUT} smul)"
DEBOLD="$(${TPUT} rmso)"
DEUL="$(${TPUT} rmul)"
RED="$(${TPUT} setaf 1)"
GREEN="$(${TPUT} setaf 2)"
YELLOW="$(${TPUT} setaf 3)"
BLUE="$(${TPUT} setaf 4)"
MAGENTA="$(${TPUT} setaf 5)"
CYAN="$(${TPUT} setaf 6)"
WHITE="$(${TPUT} setaf 7)"
GREY="$(${TPUT} setaf 8)"
NC="$(${TPUT} sgr0)"

function check_packages() {
  ${PYTHON3} -c "import termcolor" 2>/dev/null
  PKG_STATUS="${?}"
  if [[ "${PKG_STATUS}" -ne 0 ]]; then
    return 1
  fi
  return 0
}

function install_packages() {
  # Packages need to be installed
  cd "${BASE_DIR}"
  PIP="${PYTHON3_HOME}/bin/pip3"
  if [[ ! -x "${PIP}" ]]; then
    printf "%sERROR: Python virtual environment does not have the pip command: '%s'%s\n" "${RED}" "${PIP}" "${NC}"
    exit 1
  fi
  ${PIP} -r "${DEPS_FILE}"
  PIP_STATUS="${?}"
  if [[ "${PIP_STATUS}" -ne 0 ]]; then
    printf "%sERROR: Could not install required packages from: '%s'%s\n" "${RED}" "${DEPS_PATH}" "${NC}"
    exit 1
  fi
  return 0
}

if [[ "${PYTHON3}" =~ asdf ]]; then
  # Account for asdf shims
  ASDF="$(command -v asdf)"
  if [[ -z "${ASDF}" ]]; then
    printf "%sERROR: Python appears to be installed using asdf, but 'asdf' command could not be found.%s\n" "${RED}" "${NC}"
    exit 1
  fi
  PYTHON_BIN="$(asdf which python3)"
  if [[ -z "${PYTHON_BIN}" ]]; then
    printf "%sERROR: Python appears to be installed using asdf, but 'asdf which python3' command could not be found.%s\n" "${RED}" "${NC}"
    exit 1
  fi
  PYTHON3="$(realpath ${PYTHON_BIN})"
  if [[ -z "${PYTHON_HOME}" ]]; then
    PYTHON_HOME="$(dirname "$(dirname "${PYTHON3}")")"
  fi
fi

if [[ -z "${PYTHON3}" ]]; then
  printf "%sERROR: Could not find 'python3' command in path. Please add it to the path.%s\n" "${RED}" "${NC}"
  exit 1
fi

PYTHON3_HOME=""

if [[ -n "${PYTHON_HOME}" ]]; then
  PYTHON3_HOME="${PYTHON_HOME}"
else
  PYTHON3_HOME="$(dirname "$(dirname "${PYTHON3}")")"
fi

if [[ ! -d "${PYTHON3_HOME}" || ! -x "${PYTHON3_HOME}/bin/python3" ]]; then
  printf "%sERROR: Could not find 'python3' command in path. Please add it to the path.%s\n" "${RED}" "${NC}"
  exit 1
fi

PYTHON_HOME="${PYTHON3_HOME}"

if [[ -d "${BASE_DIR}" && ! -e "${VENV_SCRIPT}" && -e "${DEPS_PATH}" ]]; then
  cd "${BASE_DIR}"
  printf "%sSetting up Python virtual environment ...%s\n" "${CYAN}" "${NC}"
  ${PYTHON3} -m venv venv
  STATUS="${?}"
  if [[ "${STATUS}" -ne 0 ]]; then
    printf "%sERROR: Setting up the Python virtual environment failed with error code %d%s\n" "${RED}" "${STATUS}" "${NC}"
    exit ${STATUS}
  fi
fi

if [[ ! -e "${VENV_SCRIPT}" ]]; then
  printf "%sERROR: Could not find or create Python virtual environment at: '%s'%s\n" "${RED}" "${VENV_HOME}" "${NC}"
  exit 1
else
  printf "%sPython virtual environment created successfully at '%s'%s\n" "${CYAN}" "${VENV_HOME}" "${NC}"
fi

cd "${BASE_DIR}" || { printf "%sERROR: Could not go to base directory '%s'%s\n" "${RED}" "${BASE_DIR}" "${NC}" ; exit 1 ; }

source "${VENV_SCRIPT}"

check_packages
STATUS="${?}"
if [[ "${STATUS}" -ne 0 ]]; then
  # Packages need to be installed
  printf "%sInstalling required packages into Python virtual environment ...%s\n" "${CYAN}" "${NC}"
  install_packages
  STATUS="${?}"
  if [[ "${STATUS}" -ne 0 ]]; then
    printf "%sERROR: Python package installation failed%s\n" "${RED}" "${NC}"
    exit 1
  else
    printf "%sAll Python packages installed successfully%s\n" "${CYAN}" "${NC}"
  fi
else
  printf "%sPackages are already installed, no need to reinstall%s\n" "${CYAN}" "${NC}"
fi

check_packages
STATUS="${?}"
if [[ "${STATUS}" -ne 0 ]]; then
  printf "%sERROR: Python package installation succeeded, but packages still cannot be imported.%s\n" "${RED}" "${NC}"
  exit 1
fi

printf "\n%sPython environment and packages installed successfully%s\n" "${CYAN}" "${NC}"

printf "\n%sCreating wrapper script at '%s' ...%s\n" "${CYAN}" "${WRAPPER}" "${NC}"

cat > "${WRAPPER}" <<EOF
#!/usr/bin/env bash
TERM="${TERM}"
TPUT="${TPUT}"
RED="\$(\${TPUT} setaf 1)"
NC="\$(\${TPUT} sgr0)"
PYTHON3="${PYTHON3}"

VENV_SCRIPT="${VENV_SCRIPT}"

if [[ ! -x "\${PYTHON3}" ]]; then
  printf "%sERROR: Could not find Python executable at '%s'%s\n" "\${RED}" "\${PYTHON3}" "\${NC}"
  exit 1
fi

if [[ ! -e "\${VENV_SCRIPT}" ]]; then
  printf "%sERROR: Could not find Python virtual environment at '%s', please run install script%s\n" "\${RED}" "\${VENV_SCRIPT}" "\${NC}"
  exit 1
fi

source "\${VENV_SCRIPT}"

python3 "${SCRIPT}" "\${@}"

EOF

chmod +x "${SCRIPT}"
chmod +x "${WRAPPER}"
ln -s "${WRAPPER_NAME}" "${PROGRAM_NAME}"

printf "\n%sWrapper script created at '%s'%s\n" "${CYAN}" "${WRAPPER}" "${NC}"
printf "\n%s%s successfully installed at '%s'%s\n\n" "${GREEN}" "${PROGRAM_NAME}" "${BASE_DIR}" "${NC}"
