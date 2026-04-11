# Wiki — Azure Deployment

**VM:** `azureuser@74.178.89.28` (Ubuntu 24.04)
**Pipeline:** Azure DevOps — `azure-pipelines.yml`

---

## Initial VM Setup

### 1. Create the VM in the Azure Portal

1. Azure Portal → search bar → **"Virtual machines"** → **Create → Azure virtual machine**
2. Fill in:
   - **Resource group**: `ISEP`
   - **Virtual machine name**: `ISEP`
   - **Region**: `West Europe`
   - **Image**: `Ubuntu Server 24.04 LTS`
   - **Size**: `Standard_B2s` (2 vCPU, 4 GB RAM) or larger
   - **Administrator account**:
     - Authentication type: **SSH public key**
     - Username: `azureuser`
     - SSH public key source: **Generate new key pair**
     - Key pair name: `azure`
3. **Networking** tab:
   - Leave defaults (a new virtual network and NSG are created automatically)
4. **Review + create** → **Create**
5. When the popup **Download private key** appears → **Download private key and create resource**
   - Save the `azure.pem` file — this is the SSH key used to connect to the VM

### 2. Get the public IP

1. Azure Portal → **Virtual machines → ISEP → Overview**
2. Copy the **Public IP address**: `74.178.89.28`

### 3. Open ports in the NSG

1. Azure Portal → **Virtual machines → ISEP → Networking → Inbound port rules**
2. Add the following rules:

**Port 8000 (FastAPI backend):**
- Source: `Any`
- Destination port ranges: `8000`
- Protocol: `TCP`
- Action: `Allow`
- Priority: `310`
- Name: `Allow-Backend-8000`

**Port 80 (Nuxt frontend):**
- Source: `Any`
- Destination port ranges: `80`
- Protocol: `TCP`
- Action: `Allow`
- Priority: `321`
- Name: `Allow-Frontend-80`

**Port 5432 (PostgreSQL):**
- Source: `Any`
- Destination port ranges: `5432`
- Protocol: `TCP`
- Action: `Allow`
- Priority: `305`
- Name: `Allow-Postgres-5432`

> Port 22 (SSH) is open by default when the VM is created.

### 4. Connect to the VM and install Docker

Connect via SSH using the downloaded key:

```bash
chmod 600 azure.pem
ssh -i azure.pem azureuser@74.178.89.28
```

Install Docker:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker azureuser
# Disconnect and reconnect to apply the group
exit
ssh -i azure.pem azureuser@74.178.89.28
# Verify
docker --version
docker compose version
```

### 5. Prepare the SSH key for Azure DevOps

The downloaded key (`azure.pem`) must be uploaded to Azure DevOps Secure Files so the pipeline can use it.

1. Rename the file to `azure.key` (Azure DevOps is sensitive to the exact name used in the YAML)
2. **Azure DevOps → Pipelines → Library → Secure files → + Secure file**
3. Upload `azure.key`
4. After upload, click the file → check **Authorize for use in all pipelines** → **Save**

> Do not pass the key as an Azure DevOps variable: newlines in a PEM key are lost when copy-pasting, corrupting the format.

---

## Current Architecture (VM + Docker Compose)

```
Azure DevOps Pipeline (ubuntu-latest hosted agent)
  │
  ├── Job: test    → Python tests + coverage + ephemeral PostgreSQL service (all branches)
  │
  └── Job: deploy  → SSH to VM (main branch only, after test passes)
                      1. Download SSH key from Azure Secure Files
                      2. Generate .env locally, SCP it to the VM
                      3. rsync repo from agent to VM
                      4. DOCKER_BUILDKIT=1 docker compose up --build -d
                      5. Health checks: backend (8000) and frontend (80)

VM (74.178.89.28)
  ├── container: backend   (FastAPI, port 8000, managed by Docker Compose)
  ├── container: frontend  (Nuxt, port 80→3000, managed by Docker Compose)
  └── container: isep_simulation_db  (PostgreSQL, port 5432, permanent — NOT in Docker Compose)
```

> The PostgreSQL container runs independently of Docker Compose (`--restart always`) so it is never recreated during deployments. Data is persisted in `~/isep-app/.docker_data/postgres`.

---

## Azure DevOps Library

### Variable Group `energy-grid-prod`

`Pipelines → Library → Variable groups → energy-grid-prod`

| Variable | Type | Value |
|---|---|---|
| `VM_USER` | plain | `azureuser` *(no trailing spaces)* |
| `VM_HOST` | plain | `74.178.89.28` |
| `DATABASE_URL` | secret | `postgresql+asyncpg://isep_admin:<password>@74.178.89.28:5432/isep_db` |
| `KNMI_API_KEY` | secret | KNMI Open Data API key |
| `APP_NAME` | plain | `Energy Grid API` |
| `APP_VERSION` | plain | `0.1.0` |
| `ENVIRONMENT` | plain | `production` |

> **Database migration (2026-04-10):** La base de données a été migrée de NeonDB vers un container PostgreSQL auto-hébergé sur la VM. Seule la variable `DATABASE_URL` a changé — le `docker-compose.yml` n'a pas été modifié.

> **Warning:** Do not leave trailing spaces in values. Trailing spaces in `VM_USER` silently break SCP (error: `:/home/azureuser/isep-app/.env: No such file or directory`).

### Secure Files

`Pipelines → Library → Secure files` — file: **`azure.key`**

Private SSH key used to connect to the VM. Uploaded via the Azure DevOps UI, downloaded in the pipeline via `DownloadSecureFile@1`.

> The key cannot be stored as an Azure DevOps variable: newlines in a PEM key are lost when copy-pasting, corrupting the format.

---

## NSG — Open Ports on the VM

`Azure Portal → VM ISEP → Networking → Inbound port rules`

| Service | VM Port | NSG Rule |
|---|---|---|
| FastAPI backend | 8000 | `Allow-Backend-8000` |
| Nuxt frontend | 80 | `Allow-Frontend-80` |
| PostgreSQL | 5432 | `Allow-Postgres-5432` |

The frontend container listens on port 3000, mapped to port 80 on the VM (`80:3000` in `docker-compose.yml`).

---

## Pipeline — Deploy Steps Detail

### Step: Configure SSH key

```yaml
- script: |
    mkdir -p ~/.ssh
    cp $(sshKey.secureFilePath) ~/.ssh/vm_key
    chmod 600 ~/.ssh/vm_key
    ssh-keyscan -H $(VM_HOST) >> ~/.ssh/known_hosts 2>/dev/null
```

### Step: Push .env to VM

The `.env` is generated **on the agent** (not on the VM) to avoid interpolation issues inside SSH heredocs. `$(VAR)` are Azure DevOps macros replaced before bash executes.

```yaml
- script: |
    ssh -i ~/.ssh/vm_key -o StrictHostKeyChecking=no $(VM_USER)@$(VM_HOST) \
      "mkdir -p /home/$(VM_USER)/isep-app"
    printf "APP_NAME=%s\nAPP_VERSION=%s\nENVIRONMENT=%s\nDEBUG=false\nHOST=0.0.0.0\nPORT=8000\nDATABASE_URL=%s\nKNMI_API_KEY=%s\nNUXT_API_BASE_URL=http://backend:8000\n" \
      "$APP_NAME" "$APP_VERSION" "$ENVIRONMENT" "$DATABASE_URL" "$KNMI_API_KEY" > /tmp/.env
    scp -i ~/.ssh/vm_key -o StrictHostKeyChecking=no /tmp/.env $(VM_USER)@$(VM_HOST):/home/$(VM_USER)/isep-app/.env
  env:
    APP_NAME: $(APP_NAME)
    APP_VERSION: $(APP_VERSION)
    ENVIRONMENT: $(ENVIRONMENT)
    DATABASE_URL: $(DATABASE_URL)
    KNMI_API_KEY: $(KNMI_API_KEY)
```

Variables written to `.env` on the VM:

| Key | Value |
|---|---|
| `APP_NAME` | from Variable Group |
| `APP_VERSION` | from Variable Group |
| `ENVIRONMENT` | from Variable Group (`production`) |
| `DEBUG` | `false` (hardcoded) |
| `HOST` | `0.0.0.0` (hardcoded) |
| `PORT` | `8000` (hardcoded) |
| `DATABASE_URL` | from Variable Group (secret) |
| `KNMI_API_KEY` | from Variable Group (secret) |
| `NUXT_API_BASE_URL` | `http://backend:8000` (hardcoded — Docker Compose internal DNS) |

### Step: Deploy via Docker Compose

rsync syncs the repo from the agent to the VM (avoids git auth issues with private Azure DevOps repos), then runs Docker Compose.

```bash
DOCKER_BUILDKIT=1 sudo -E docker compose up --build -d
```

- `DOCKER_BUILDKIT=1`: enables layer caching for `--mount=type=cache` directives
- `sudo -E`: preserves environment variables (including `DOCKER_BUILDKIT`)

---

## Optional Script: `scripts/install-agent.sh`

Script to install a **self-hosted Azure DevOps agent** on the VM. Not used by the current pipeline (which runs on `ubuntu-latest` hosted agent).

Useful if you want the pipeline to run directly on the VM without an Azure DevOps-hosted agent.

### Usage

```bash
./scripts/install-agent.sh <org_url> <pat> <pool_name>
```

- `org_url`: Azure DevOps organization URL (e.g. `https://dev.azure.com/my-org`)
- `pat`: Personal Access Token with scope **Agent Pools: Read & manage**
- `pool_name`: agent pool name (e.g. `ISEP-VM`)

### Behavior

- **Idempotent**: checks `systemctl is-active azure-pipelines-agent` before installing — does nothing if the agent is already running
- Downloads the agent from GitHub releases (`v3.236.1`)
- Accepts `AGENT_TAR_PATH` as an environment variable to use a pre-downloaded tarball (workaround for VMs without internet access to Azure CDN)
- Installs the agent as a systemd service via `svc.sh`

### Create the PAT for the agent

1. Azure DevOps → **Avatar (top right) → Personal access tokens → New Token**
2. Name: `isep-vm-agent`
3. Scopes: **Agent Pools → Read & manage**
4. Copy the generated value

### Create the agent pool

1. Azure DevOps → **Project settings → Agent pools → Add pool**
2. Type: **Self-hosted**
3. Name: `ISEP-VM`
4. Check **Grant access permission to all pipelines**

---

## PostgreSQL on VM (migration from NeonDB)

**Date:** 2026-04-10

The database was migrated from NeonDB (cloud) to a self-hosted PostgreSQL container on the VM. The container runs independently of Docker Compose so it is never recreated during deployments.

### Create the PostgreSQL container

```bash
docker run -d \
  --name isep_simulation_db \
  --restart always \
  -e POSTGRES_USER='isep_admin' \
  -e POSTGRES_PASSWORD='<password>' \
  -e POSTGRES_DB='isep_db' \
  -v ~/isep-app/.docker_data/postgres:/var/lib/postgresql \
  -p 5432:5432 \
  postgres:latest
```

- `--restart always`: container survives VM reboots and Docker daemon restarts
- `-v ~/isep-app/.docker_data/postgres`: data persisted on the VM disk
- `-p 5432:5432`: exposed externally (NSG rule `Allow-Postgres-5432` required)

### Restore the NeonDB backup

```bash
# Copy backup from local machine to VM
scp -i azure.pem neondb_backup_2026-04-10_11-45.tar azureuser@74.178.89.28:~

# Copy backup into the container
docker cp neondb_backup_2026-04-10_11-45.tar isep_simulation_db:/tmp/backup.tar

# Restore
docker exec -it isep_simulation_db pg_restore -U isep_admin -d isep_db --no-owner --no-privileges /tmp/backup.tar

# Verify
docker exec -it isep_simulation_db psql -U isep_admin -d isep_db -c "SELECT COUNT(*) FROM public.supplies;"

# Cleanup
rm ~/neondb_backup_2026-04-10_11-45.tar
```

### Update Variable Group

In `Pipelines → Library → energy-grid-prod`, update `DATABASE_URL`:

```
postgresql+asyncpg://isep_admin:<password>@74.178.89.28:5432/isep_db
```

No changes to `docker-compose.yml` were needed — the database is referenced only via `DATABASE_URL`.

---

## Issues Encountered

### SSH key corrupted when stored as an Azure DevOps variable

**Problem:** `error in libcrypto` — newlines in the PEM key are lost when pasting into a secret variable.

**Fix:** Upload the key file via `Pipelines → Library → Secure Files` and download it with `DownloadSecureFile@1`.

### Divergent branches on VM after force-push

**Problem:** `fatal: Need to specify how to reconcile divergent branches` with `git pull`.

**Fix:** Replace `git pull` with `git fetch --all && git reset --hard origin/main`.

### Git auth fails from the VM on a private Azure DevOps repo

**Problem:** `git clone` from the VM requires Azure DevOps authentication.

**Fix:** Use `rsync` from the agent (which already has the checkout) to the VM — no git auth needed on the VM.

### Azure DevOps variables not interpolated inside SSH heredocs

**Problem:** `$(DATABASE_URL)` is not expanded inside a heredoc passed over SSH.

**Fix:** Generate the `.env` locally with `printf` and transfer it via SCP as a separate step.

### Trailing spaces in Variable Group values

**Problem:** `VM_USER` with trailing spaces → SCP silently fails, error: `:/home/azureuser/isep-app/.env: No such file or directory`.

**Fix:** Check and remove trailing spaces in `Pipelines → Library → energy-grid-prod`.

---

## Verify the Deployment

From the VM:
```bash
docker ps                          # 3 containers: backend, frontend, isep_simulation_db
curl http://localhost:8000/health  # {"status":"ok"}
curl -s http://localhost:80 | head # Nuxt HTML
docker exec isep_simulation_db psql -U isep_admin -d isep_db -c "\l"  # DB accessible
```

From the internet:
```
http://74.178.89.28:8000/health  → {"status":"ok"}
http://74.178.89.28              → Nuxt frontend (port 80)
```

---

---

# Planned Migration: VM → Azure Container Registry + Container Instances

**Status: on hold** — blocked at step 2.2.1 (Managed Identity creation) due to insufficient permissions on the Azure tenant.

## Target Architecture

```
Azure DevOps Pipeline (ubuntu-latest hosted agent)
  │
  ├── Job: test           → Python tests (unchanged)
  │
  ├── Job: build_and_push → docker build + push to ACR
  │                         (backend + frontend)
  │
  └── Job: deploy         → az container create on ACI
                            (backend then frontend)
```

## Why Migrate

| Aspect | Current VM | ACR + ACI |
|---|---|---|
| Infrastructure to manage | VM, OS, Docker, SSH | Nothing |
| Cost | VM running 24/7 | Billed per second of use |
| Secrets | `.env` via SSH | Azure DevOps variables → ACI env |
| Logs | `docker logs` on VM | Logs tab in Azure Portal |
| Networking | Internal Docker Compose DNS | Separate public IPs |

---

## Step 1 — Create the Azure Container Registry

### 1.1 Create the registry

1. Azure Portal → search bar → **"Container registries"** → **Create**
2. Fill in:
   - **Resource group**: `ISEP`
   - **Registry name**: `isepregistry` *(globally unique)*
   - **Region**: `West Europe`
   - **Pricing plan**: `Basic`
3. **Review + create** → **Create**

### 1.2 Enable the admin account

1. Open registry `isepregistry`
2. Left menu → **Access keys**
3. Enable the **Admin user** toggle
4. Note:
   - **Login server**: `isepregistry.azurecr.io`
   - **Username**: `isepregistry`
   - **Password**: copy either password

---

## Step 2 — Configure Azure DevOps

### 2.1 Update the Variable Group

1. **Pipelines → Library → `energy-grid-prod`**
2. Delete VM variables: `VM_USER`, `VM_HOST`, `VM_SSH_KEY` (if present)
3. Add:

| Variable | Value | Secret |
|---|---|---|
| `ACR_LOGIN_SERVER` | `isepregistry.azurecr.io` | no |
| `ACR_USERNAME` | `isepregistry` | yes |
| `ACR_PASSWORD` | *(password from step 1.2)* | yes |
| `ACI_RESOURCE_GROUP` | `ISEP` | no |

4. Keep: `DATABASE_URL`, `KNMI_API_KEY`, `APP_NAME`, `APP_VERSION`, `ENVIRONMENT`
5. **Save**

### 2.2 Create the Managed Identity *(blocked — insufficient permissions)*

> The "App registration (automatic)" method is rejected on this tenant (missing Entra ID permissions). A **Managed Identity** is required instead.

#### 2.2.1 Create the Managed Identity

1. Azure Portal → **"Managed Identities"** → **Create**
2. Fill in:
   - **Resource group**: `ISEP`
   - **Region**: `West Europe`
   - **Name**: `isep-devops-identity`
3. **Review + create** → **Create**

#### 2.2.2 Assign the Contributor role

1. Azure Portal → **Resource groups → ISEP → Access control (IAM)**
2. **Add → Add role assignment**
3. Role: **Contributor** → Next
4. **Members → Select members** → search `isep-devops-identity` → Select
5. **Review + assign**

#### 2.2.3 Create the Service Connection

1. **Project settings → Service connections → New service connection**
2. Type: **Azure Resource Manager** → Next
3. Method: **Managed identity** *(3rd option)* → Next
4. Select `isep-devops-identity`
5. Name: `ISEP-Azure-Connection`
6. Check **Grant access permission to all pipelines**
7. **Save**

### 2.3 Delete the SSH Secure File

1. **Pipelines → Library → Secure files**
2. `azure.key` → **Delete**

---

## Step 3 — Update `azure-pipelines.yml`

Replace the entire file content with:

```yaml
trigger:
  branches:
    include:
      - main

pr:
  branches:
    include:
      - '*'

variables:
  - group: energy-grid-prod
  - name: IMAGE_TAG
    value: $(Build.BuildId)

jobs:

  - job: test
    displayName: 'Test'
    pool:
      vmImage: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpassword
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-retries 5
    steps:
      - task: UsePythonVersion@0
        inputs:
          versionSpec: '3.11'
      - script: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
        displayName: 'Install dependencies'
      - script: |
          pytest tests/ -v --junitxml=test-results.xml
        displayName: 'Run tests'
        env:
          DATABASE_URL: postgresql+asyncpg://testuser:testpassword@localhost:5432/testdb
          ENVIRONMENT: testing
      - task: PublishTestResults@2
        inputs:
          testResultsFormat: JUnit
          testResultsFiles: test-results.xml
        condition: always()

  - job: build_and_push
    displayName: 'Build & Push to ACR'
    dependsOn: test
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    pool:
      vmImage: ubuntu-latest
    steps:
      - script: |
          docker login $(ACR_LOGIN_SERVER) -u $(ACR_USERNAME) -p $(ACR_PASSWORD)
        displayName: 'Login to ACR'
      - script: |
          docker build \
            -t $(ACR_LOGIN_SERVER)/backend:$(IMAGE_TAG) \
            -t $(ACR_LOGIN_SERVER)/backend:latest \
            -f app/Dockerfile .
          docker push $(ACR_LOGIN_SERVER)/backend:$(IMAGE_TAG)
          docker push $(ACR_LOGIN_SERVER)/backend:latest
        displayName: 'Build & push backend'
      - script: |
          docker build \
            -t $(ACR_LOGIN_SERVER)/frontend:$(IMAGE_TAG) \
            -t $(ACR_LOGIN_SERVER)/frontend:latest \
            ./energy-dashboard
          docker push $(ACR_LOGIN_SERVER)/frontend:$(IMAGE_TAG)
          docker push $(ACR_LOGIN_SERVER)/frontend:latest
        displayName: 'Build & push frontend'

  - job: deploy
    displayName: 'Deploy to ACI'
    dependsOn: build_and_push
    condition: succeeded()
    pool:
      vmImage: ubuntu-latest
    steps:
      - task: AzureCLI@2
        displayName: 'Deploy backend'
        inputs:
          azureSubscription: 'ISEP-Azure-Connection'
          scriptType: bash
          scriptLocation: inlineScript
          inlineScript: |
            az container create \
              --resource-group $(ACI_RESOURCE_GROUP) \
              --name energy-backend \
              --image $(ACR_LOGIN_SERVER)/backend:latest \
              --registry-login-server $(ACR_LOGIN_SERVER) \
              --registry-username $(ACR_USERNAME) \
              --registry-password $(ACR_PASSWORD) \
              --cpu 1 --memory 1 \
              --ports 8000 \
              --ip-address Public \
              --environment-variables \
                APP_NAME="$(APP_NAME)" \
                APP_VERSION="$(APP_VERSION)" \
                ENVIRONMENT=production \
                HOST=0.0.0.0 PORT=8000 \
              --secure-environment-variables \
                DATABASE_URL="$(DATABASE_URL)" \
                KNMI_API_KEY="$(KNMI_API_KEY)" \
              --restart-policy Always \
              --output table

      - task: AzureCLI@2
        displayName: 'Deploy frontend'
        inputs:
          azureSubscription: 'ISEP-Azure-Connection'
          scriptType: bash
          scriptLocation: inlineScript
          inlineScript: |
            BACKEND_IP=$(az container show \
              --resource-group $(ACI_RESOURCE_GROUP) \
              --name energy-backend \
              --query ipAddress.ip -o tsv)
            az container create \
              --resource-group $(ACI_RESOURCE_GROUP) \
              --name energy-frontend \
              --image $(ACR_LOGIN_SERVER)/frontend:latest \
              --registry-login-server $(ACR_LOGIN_SERVER) \
              --registry-username $(ACR_USERNAME) \
              --registry-password $(ACR_PASSWORD) \
              --cpu 1 --memory 1 \
              --ports 80 \
              --ip-address Public \
              --environment-variables \
                NUXT_API_BASE_URL="http://${BACKEND_IP}:8000" \
                NODE_ENV=production \
              --restart-policy Always \
              --output table

      - task: AzureCLI@2
        displayName: 'Health checks'
        inputs:
          azureSubscription: 'ISEP-Azure-Connection'
          scriptType: bash
          scriptLocation: inlineScript
          inlineScript: |
            BACKEND_IP=$(az container show \
              --resource-group $(ACI_RESOURCE_GROUP) \
              --name energy-backend \
              --query ipAddress.ip -o tsv)
            FRONTEND_IP=$(az container show \
              --resource-group $(ACI_RESOURCE_GROUP) \
              --name energy-frontend \
              --query ipAddress.ip -o tsv)
            for i in $(seq 1 12); do
              curl -sf "http://${BACKEND_IP}:8000/health" && echo "Backend OK" && break
              sleep 10
            done
            for i in $(seq 1 12); do
              curl -sf "http://${FRONTEND_IP}/" && echo "Frontend OK" && break
              sleep 10
            done
            echo "Backend  : http://${BACKEND_IP}:8000"
            echo "Frontend : http://${FRONTEND_IP}/"
```

---

## Step 4 — Verify after ACI deployment

1. **Azure Portal → Container instances**
2. Two containers visible: `energy-backend` and `energy-frontend`
3. Click each container → **Overview** → copy the **Public IP address**
4. Test in browser:
   - `http://<BACKEND_IP>:8000/health` → `{"status":"ok"}`
   - `http://<FRONTEND_IP>/` → Nuxt page
5. To check logs on failure: container → **Containers** → **Logs**

---

## Step 5 — Full VM cleanup

Once ACI is in production, remove all traces of the VM.

### 5.1 Delete the VM

1. **Azure Portal → Virtual machines → ISEP**
2. **Delete**
3. Check **all** boxes:
   - OS disk
   - Network interface
   - Public IP address
   - Network security group *(if dedicated to this VM)*
4. Confirm the name → **Delete**

### 5.2 Verify the Resource Group

1. **Azure Portal → Resource groups → ISEP**
2. Ensure the following resources are gone:
   - Virtual machine
   - Disk (`ISEP_OsDisk_...`)
   - Network interface
   - Public IP address
   - VM NSG
3. Manually delete any remaining resources

### 5.3 Clean up Azure DevOps

1. **Pipelines → Library → Secure files** → delete `azure.key` if still present
2. **Pipelines → Library → `energy-grid-prod`** → delete `VM_USER`, `VM_HOST` if still present
3. **Project settings → Agent pools** → delete pool `ISEP-VM` if it exists

### 5.4 Final verification

- Resource group `ISEP` contains only: ACR `isepregistry`, containers `energy-backend`, `energy-frontend`, Managed Identity `isep-devops-identity`
- IP `74.178.89.28` is no longer reachable
