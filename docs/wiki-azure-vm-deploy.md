# Wiki — Azure VM Deployment via Azure DevOps Pipeline

**Date:** 2026-04-09
**VM:** `azureuser@74.178.89.28` (Ubuntu 24.04)

---

## Architecture

```
Azure DevOps Pipeline (ubuntu-latest hosted agent)
  │
  ├── Job: test    → Python tests + ephemeral PostgreSQL service
  │
  └── Job: deploy  → SSH to VM (main branch only, after test passes)
                      1. Download SSH key from Azure Secure Files
                      2. Generate .env locally, SCP it to the VM
                      3. git fetch + reset --hard origin/main (or clone)
                      4. DOCKER_BUILDKIT=1 docker compose up --build -d
                      5. Health checks: backend (8000) and frontend (80)
```

---

## Azure DevOps Variable Group

Name: **`energy-grid-prod`** — `Pipelines → Library`

| Variable | Type | Description |
|---|---|---|
| `VM_USER` | plain | `azureuser` |
| `VM_HOST` | plain | `74.178.89.28` |
| `DATABASE_URL` | secret | Database connection string (`postgresql+asyncpg://...`) |
| `KNMI_API_KEY` | secret | KNMI Open Data API key |
| `APP_NAME` | plain | `Energy Grid API` |
| `APP_VERSION` | plain | `0.1.0` |
| `ENVIRONMENT` | plain | `production` |

---

## Secure Files

`Pipelines → Library → Secure files` — file: **`azure.key`**

Contains the private SSH key used to connect to the VM. Uploaded via the Azure DevOps UI and downloaded in the pipeline via `DownloadSecureFile@1`.

> The key cannot go through a regular Azure DevOps variable: newlines are lost when pasting a PEM key, which corrupts the format.

---

## NSG Ports (Azure Network Security Group)

| Service | Container port | VM port | NSG rule |
|---|---|---|---|
| Backend FastAPI | 8000 | 8000 | `Allow-Backend-8000` |
| Frontend Nuxt | 3000 | 80 | `Allow-Frontend-80` |

The frontend container listens on 3000, mapped to port 80 on the VM (`80:3000` in `docker-compose.yml`).

---

## Key Files

### `azure-pipelines.yml`

Two jobs:

**Job `test`** — all branches and PRs:
- Ephemeral PostgreSQL service container
- `pytest` with XML coverage and JUnit results

**Job `deploy`** — `main` branch only, depends on `test`:

```yaml
steps:
  - task: DownloadSecureFile@1      # Downloads azure.key
  - script: Configure SSH key       # cp, chmod 600, ssh-keyscan
  - script: Push .env to VM         # printf > /tmp/.env, scp to VM
  - script: Deploy via Docker Compose  # git fetch/reset + docker compose up
  - script: Health checks           # curl backend:8000 + frontend:80
```

#### .env generation

The `.env` is built **on the hosted agent** (not on the VM) to avoid variable interpolation issues inside SSH heredocs:

```bash
printf "APP_NAME=%s\nAPP_VERSION=%s\nENVIRONMENT=%s\nDEBUG=false\nHOST=0.0.0.0\nPORT=8000\nDATABASE_URL=%s\nKNMI_API_KEY=%s\nNUXT_API_BASE_URL=http://backend:8000\n" \
  "$APP_NAME" "$APP_VERSION" "$ENVIRONMENT" "$DATABASE_URL" "$KNMI_API_KEY" > /tmp/.env
scp -i ~/.ssh/vm_key -o StrictHostKeyChecking=no /tmp/.env $(VM_USER)@$(VM_HOST):/home/$(VM_USER)/isep-app/.env
```

#### Repo update on the VM

```bash
if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" fetch --all
  git -C "$REPO_DIR" reset --hard origin/main
else
  git clone '$AUTH_URL' "$REPO_DIR"
fi
```

`reset --hard` is used instead of `git pull` because the branch can have divergent history after a force-push.

The repo URL is built with the Azure DevOps PAT (`SYSTEM_ACCESSTOKEN`) to access the private repo:

```bash
AUTH_URL=$(echo "$CLEAN_URI" | sed "s|https://|https://pat:${SYSTEM_ACCESSTOKEN}@|")
```

#### Docker deployment

```bash
DOCKER_BUILDKIT=1 sudo -E docker compose up --build -d
```

- `DOCKER_BUILDKIT=1`: enables layer caching for `--mount=type=cache` directives
- `sudo -E`: preserves environment variables (including `DOCKER_BUILDKIT`)

### `docker-compose.yml`

```yaml
services:
  backend:
    build: { context: ., dockerfile: app/Dockerfile }
    ports: ["8000:8000"]
    env_file: .env

  frontend:
    build: { context: ./energy-dashboard, dockerfile: Dockerfile }
    ports: ["80:3000"]          # exposed on port 80 (HTTP default)
    environment:
      NUXT_API_BASE_URL: http://backend:8000
    depends_on: [backend]
```

### `energy-dashboard/Dockerfile`

pnpm store is cached between builds using a BuildKit mount:

```dockerfile
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml* ./
RUN --mount=type=cache,id=pnpm,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile
```

### `scripts/install-agent.sh`

**Optional** script to install a self-hosted Azure DevOps agent on the VM. Not used by the current pipeline (which uses `ubuntu-latest` hosted agents).

Usage:
```bash
./scripts/install-agent.sh <org_url> <pat> <pool_name>
```

- Idempotent: checks `systemctl is-active azure-pipelines-agent` before installing
- Accepts `AGENT_TAR_PATH` env var to use a pre-downloaded tarball (workaround for VMs without internet access to Azure CDN)
- Installs and starts a systemd service via `svc.sh`

---

## Issues Encountered and Fixes

### SSH key corrupted when passed as an Azure DevOps variable

**Problem:** `error in libcrypto` — newlines in the PEM key are lost when pasting into an Azure DevOps secret variable.

**Fix:** Upload the key file via `Pipelines → Library → Secure Files` and download it with `DownloadSecureFile@1`.

### Agent tarball unreachable from the VM

**Problem:** `vstsagentpackage.azureedge.net` not reachable from the VM. GitHub releases returned 404 for some versions.

**Fix:** Download the tarball on the hosted agent (which has internet access), SCP it to the VM, and use `AGENT_TAR_PATH` in the install script.

### Azure DevOps variables not interpolated inside SSH heredocs

**Problem:** Variables like `$(DATABASE_URL)` are not expanded inside an SSH heredoc passed with `bash -s`.

**Fix:** Generate the `.env` locally with `printf` and transfer it via SCP as a separate pipeline step.

### Divergent branches on VM after force-push

**Problem:** `fatal: Need to specify how to reconcile divergent branches` with `git pull`.

**Fix:** Replace `git pull` with `git fetch --all && git reset --hard origin/main`.

---

## Verifying the Deployment

From the VM:
```bash
docker ps                          # 2 running containers
curl http://localhost:8000/health  # {"status":"ok"}
curl -s http://localhost:80 | head # Nuxt HTML
```

From the internet:
```
http://74.178.89.28:8000/health  → {"status":"ok"}
http://74.178.89.28              → Nuxt frontend (port 80)
```
