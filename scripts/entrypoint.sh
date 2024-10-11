#!/bin/bash

############################################################################
# Entrypoint script for the Phidata image
############################################################################

INIT_PHI=${INIT_PHI:=True}
SETUP_WS=${SETUP_WS:=False}

############################################################################
# Install dependencies
############################################################################

if [[ "$INSTALL_REQUIREMENTS" = true || "$INSTALL_REQUIREMENTS" = True ]]; then
  echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
  echo "Installing requirements from $REQUIREMENTS_FILE_PATH"
  pip3 install -r $REQUIREMENTS_FILE_PATH
  echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
fi

############################################################################
# Setup workspace
############################################################################

if [[ "$SETUP_WS" = true || "$SETUP_WS" = True ]]; then
  echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
  echo "Setting up workspace: $WORSPACE_DIR"
  cd ${WORSPACE_DIR}
  phi ws setup
  echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
fi

############################################################################
# Start the machine
############################################################################

case "$1" in
  chill)
    ;;
  *)
    exec "$@"
    ;;
esac

echo ">>> Welcome!"
while true; do sleep 18000; done
