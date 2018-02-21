mkdir -p "${PREFIX}"/include/Arduino

# Generate Arduino `library.properties` file
python -m paver generate_arduino_library_properties
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
# Copy Arduino library to Conda include directory
cp -ra "${SRC_DIR}"/arduino_rpc/Arduino/library/ArduinoRpc "${PREFIX}"/include/Arduino/ArduinoRpc
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

# Generate `setup.py` from `pavement.py` definition.
python -m paver generate_setup
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

# Install source directory as Python package.
python setup.py install --single-version-externally-managed --record record.txt
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
