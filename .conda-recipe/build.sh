mkdir -p "${PREFIX}"/include/Arduino

# Generate Arduino `library.properties` file
"${PYTHON}" -m paver generate_arduino_library_properties
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
# Copy Arduino library to Conda include directory
cp -ra "${SRC_DIR}"/arduino_rpc/Arduino/library/ArduinoRpc "${PREFIX}"/include/Arduino/ArduinoRpc
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

# Generate `setup.py` from `pavement.py` definition.
"${PYTHON}" -m paver generate_setup
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

# **Workaround** `conda build` runs a copy of `setup.py` named
# `conda-build-script.py` with the recipe directory as the only argument.
# This causes paver to fail, since the recipe directory is not a valid paver
# task name.
#
# We can work around this by wrapping the original contents of `setup.py` in
# an `if` block to only execute during package installation.
"${PYTHON}" -c "from __future__ import print_function; input_ = open('setup.py', 'r'); data = input_.read(); input_.close(); output_ = open('setup.py', 'w'); output_.write('\n'.join(['import sys', 'import path_helpers as ph', '''if ph.path(sys.argv[0]).name == 'conda-build-script.py':''', '    sys.argv.pop()', 'else:', '\n'.join([('    ' + d) for d in data.splitlines()])])); output_.close(); print(open('setup.py', 'r').read())"

# Install source directory as Python package.
"${PYTHON}" -m pip install --no-cache .
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
