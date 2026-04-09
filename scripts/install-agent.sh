#!/usr/bin/env bash
# Install Azure Pipelines self-hosted agent on Ubuntu
# Usage: install-agent.sh <org_url> <pat> <pool_name>
set -euo pipefail

ORG_URL="$1"
PAT="$2"
POOL_NAME="$3"
AGENT_DIR="$HOME/azure-agent"
AGENT_VERSION="3.236.1"

# Already installed and running?
if systemctl is-active --quiet azure-pipelines-agent 2>/dev/null; then
  echo "Agent already running, skipping installation."
  exit 0
fi

echo "==> Installing Azure Pipelines agent v${AGENT_VERSION}"
mkdir -p "$AGENT_DIR"
cd "$AGENT_DIR"

curl -fsSL \
  "https://vstsagentpackage.azureedge.net/agent/${AGENT_VERSION}/vsts-agent-linux-x64-${AGENT_VERSION}.tar.gz" \
  -o agent.tar.gz
tar xzf agent.tar.gz
rm agent.tar.gz

echo "==> Configuring agent"
./config.sh \
  --unattended \
  --url "$ORG_URL" \
  --auth pat \
  --token "$PAT" \
  --pool "$POOL_NAME" \
  --agent "$(hostname)" \
  --replace \
  --acceptTeeEula

echo "==> Installing as systemd service"
sudo ./svc.sh install
sudo ./svc.sh start

echo "==> Agent installed and started"
