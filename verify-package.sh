#!/usr/bin/env bash
# verify-package.sh – Install a DEB or RPM package and validate that its main binary is available.
# Usage: verify-package.sh <package-path> <binary-name>
# Arguments:
#   package-path : Absolute or relative path to the .deb or .rpm package file.
#   binary-name  : Name of the binary expected to appear in $PATH after installation.

set -euo pipefail

# Detect if the script is running as root. If not, prefix privileged commands with sudo.
if [[ $(id -u) -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

PKG_PATH=${1:-}
BINARY=${2:-}

if [[ -z "$PKG_PATH" || -z "$BINARY" ]]; then
  echo "Usage: verify-package.sh <package-path> <binary-name>"
  exit 2
fi

# Detect package type by file extension
if [[ "$PKG_PATH" == *.deb ]]; then
  echo "Detected DEB package: $PKG_PATH"
  $SUDO apt-get update -y
  # Try to install; if dependencies are missing, apt-get -f install resolves them.
  $SUDO dpkg -i "$PKG_PATH" || $SUDO apt-get -f install -y
elif [[ "$PKG_PATH" == *.rpm ]]; then
  echo "Detected RPM package: $PKG_PATH"
  # Ensure yum/dnf exists – older CentOS uses yum, newer may have dnf.
  if command -v dnf >/dev/null 2>&1; then
    $SUDO dnf -y install "$PKG_PATH"
  else
    $SUDO yum -y localinstall "$PKG_PATH"
  fi
else
  echo "Unsupported package format: $PKG_PATH"
  exit 3
fi

# Start the Milvus service if systemctl is available
if command -v systemctl >/dev/null 2>&1; then
  echo "Starting Milvus service..."
  $SUDO systemctl start milvus
  echo "Milvus service started."
fi

# Verify the binary is available in PATH
if command -v "$BINARY" >/dev/null 2>&1; then
  echo "$BINARY found in PATH – installation succeeded."
else
  echo "ERROR: $BINARY not found after installation."
  exit 4
fi

# ----------------------------------------
# Python hello_milvus validation using uv
# ----------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install uv if not present
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found, installing..."
  curl -Ls https://astral.sh/uv/install.sh | bash
  # uv install script typically installs to ~/.cargo/bin; ensure it's in PATH
  export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create isolated virtual environment and install dependencies
cd "${SCRIPT_DIR}"
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run hello_milvus.py 并在失败时收集 Milvus 状态与日志
if python hello_milvus.py --host 127.0.0.1; then
  echo "hello_milvus validation completed successfully."
else
  echo "hello_milvus validation failed"

  # ----------------------------------------
  # Display Milvus service status and collect logs
  # ----------------------------------------
  SERVICE_NAME="milvus"
  LOG_DIR="${SCRIPT_DIR}/milvus-debug-logs"
  mkdir -p "$LOG_DIR"

  if command -v systemctl >/dev/null 2>&1 && systemctl list-units --type=service | grep -q "$SERVICE_NAME"; then
    echo "\n---- Milvus Service Status ----" | tee "$LOG_DIR/status.txt"
    systemctl --no-pager -l status "$SERVICE_NAME" | tee -a "$LOG_DIR/status.txt" || true

    echo "\n---- Recent Milvus Logs (last 200 lines) ----" | tee "$LOG_DIR/journal.txt"
    journalctl -u "$SERVICE_NAME" --no-pager -n 200 | tee -a "$LOG_DIR/journal.txt" || true
  else
    echo "Milvus service not managed by systemd or not found." | tee "$LOG_DIR/status.txt"
  fi

  echo "Collected Milvus status and logs under $LOG_DIR" >&2
  exit 5
fi
