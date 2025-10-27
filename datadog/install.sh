#!/bin/bash

# Define source files (relative to script location)
LOCAL_CHECK_FILE="checks.d/temperatures.py"
LOCAL_CONF_FILE="conf.d/temperatures.yaml"
LOCAL_SUDOERS_FILE="sudoers.d/dd-temperatures-smartctl"

# Define destination paths on the local machine
DEST_CHECK_DIR="/etc/datadog-agent/checks.d/"
DEST_CONF_DIR="/etc/datadog-agent/conf.d/"
DEST_SUDOERS_DIR="/etc/sudoers.d/"

# Ensure destination directories exist
sudo mkdir -p "${DEST_CHECK_DIR}"
sudo mkdir -p "${DEST_CONF_DIR}"
sudo mkdir -p "${DEST_SUDOERS_DIR}"

# Copy check file
echo "Copying ${LOCAL_CHECK_FILE} to ${DEST_CHECK_DIR}"
sudo cp "${LOCAL_CHECK_FILE}" "${DEST_CHECK_DIR}"

# Copy configuration file
echo "Copying ${LOCAL_CONF_FILE} to ${DEST_CONF_DIR}"
sudo cp "${LOCAL_CONF_FILE}" "${DEST_CONF_DIR}"

# Copy sudoers file
echo "Copying ${LOCAL_SUDOERS_FILE} to ${DEST_SUDOERS_DIR}"
sudo cp "${LOCAL_SUDOERS_FILE}" "${DEST_SUDOERS_DIR}"

# Restart Datadog agent
echo "Restarting Datadog agent"
sudo systemctl restart datadog-agent

echo "Installation script finished."
