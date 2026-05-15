# Testing Guide

Trois niveaux de test, à faire dans l'ordre :

1. **Local** — orchestrateur sur ta machine, simuler un run manuellement via l'API
2. **Provisioning** — terraform crée la VM, orchestrateur démarre dessus
3. **End-to-end** — pipeline CI complète, bench réel, leaderboard dans S3

---

## Test 0 — Orchestrateur en local

Le plus rapide pour valider le code sans toucher à l'infra.

### Démarrer la stack

```bash
cp .env.example .env
```

Remplir `.env` (valeurs minimales) :

```env
POSTGRES_USER=llmgrill
POSTGRES_PASSWORD=changeme
ORCHESTRATOR_URL=http://localhost:8000
API_KEY=local
HF_TOKEN=                  # laisser vide si pas de vrai bench
SCW_ACCESS_KEY=            # laisser vide si pas d'upload S3
SCW_SECRET_KEY=
SCW_BUCKET=llmgrill-results
SCW_REGION=fr-par
GPU_ZONE=fr-par-2
DEBUG=true                 # active /docs et /redoc
```

```bash
make up
# postgres + migrations + orchestrator démarrent
# logs en direct : make up-debug
```

Vérifier :

```bash
curl http://localhost:8000/health
# → {"status":"ok"}

# Swagger UI (disponible uniquement si DEBUG=true)
open http://localhost:8000/docs
```

### Simuler un run complet sans GPU

L'objectif : valider que le cycle run → complete → leaderboard fonctionne,
sans spawner de vraie VM GPU.

**1. Créer un run manuellement**

```bash
API_KEY=local

curl -s -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${API_KEY}" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "model_size_b": 8,
    "engine": "vllm",
    "scenario_path": "scenarios/basic_8b.yaml"
  }' | tee /tmp/run.json

RUN_ID=$(jq -r '.id' /tmp/run.json)
echo "Run ID: ${RUN_ID}"
```

**2. Enregistrer un node fictif**

```bash
curl -s -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${API_KEY}" \
  -d "{
    \"id\": \"node-${RUN_ID}\",
    \"gpu_type\": \"L40S\",
    \"gpu_count\": 1
  }"
```

**3. Poster des résultats fictifs**

```bash
RESULTS_JSONL='{"prompt_tokens":100,"completion_tokens":50,"ttft_s":0.12,"tpot_s":0.03,"e2e_s":0.42,"success":true}
{"prompt_tokens":100,"completion_tokens":48,"ttft_s":0.11,"tpot_s":0.03,"e2e_s":0.40,"success":true}'

curl -s -X POST "http://localhost:8000/runs/${RUN_ID}/complete" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${API_KEY}" \
  -d "{\"results_jsonl\": $(echo "${RESULTS_JSONL}" | jq -Rs .)}"
```

**4. Vérifier le leaderboard**

```bash
curl -s http://localhost:8000/leaderboard | jq .
```

Le run doit apparaître avec ses métriques. Si la liste est vide, vérifier les logs :

```bash
make logs
```

### Arrêter

```bash
make down          # conserve les volumes (DB intacte)
make down-volumes  # wipe complet
```

---

## Test 1 — Provisioning local

Valide que Terraform crée la VM, que cloud-init installe Docker, et que l'orchestrateur démarre.
**Aucun benchmark ne tourne** — on vérifie juste que la VM est up et `/health` répond.

### Prérequis

- Terraform ≥ 1.6 installé (`terraform --version`)
- Credentials Scaleway disponibles
- Une clé SSH ED25519 locale

```bash
# Vérifier que les outils sont présents
terraform --version
aws --version   # pour le backend S3 (AWS CLI)
ssh -V
```

### Étape 1 — Créer le bucket tfstate (une seule fois)

```bash
AWS_ACCESS_KEY_ID=<SCW_ACCESS_KEY> \
AWS_SECRET_ACCESS_KEY=<SCW_SECRET_KEY> \
aws s3api create-bucket \
  --bucket llmgrill-tfstate \
  --endpoint-url https://s3.fr-par.scw.cloud
```

Si le bucket existe déjà, cette commande retourne une erreur ignorable.

### Étape 2 — Créer `infra/terraform.tfvars`

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
```

Remplir `infra/terraform.tfvars` :

```hcl
region        = "fr-par"
zone          = "fr-par-1"
instance_type = "DEV1-M"
deploy_user   = "deploy"

ssh_public_keys = [
  "ssh-ed25519 AAAA...",   # ta clé publique : cat ~/.ssh/id_ed25519.pub
]

admin_cidrs = [
  "X.X.X.X/32",   # ton IP publique : curl -s ifconfig.me
]
```

> `infra/terraform.tfvars` est dans `.gitignore` — ne pas commiter.

### Étape 3 — Init et apply

```bash
cd infra

AWS_ACCESS_KEY_ID=<SCW_ACCESS_KEY> \
AWS_SECRET_ACCESS_KEY=<SCW_SECRET_KEY> \
SCW_ACCESS_KEY=<SCW_ACCESS_KEY> \
SCW_SECRET_KEY=<SCW_SECRET_KEY> \
terraform init

AWS_ACCESS_KEY_ID=<SCW_ACCESS_KEY> \
AWS_SECRET_ACCESS_KEY=<SCW_SECRET_KEY> \
SCW_ACCESS_KEY=<SCW_ACCESS_KEY> \
SCW_SECRET_KEY=<SCW_SECRET_KEY> \
terraform apply
```

Terraform affiche l'IP publique à la fin :

```
Outputs:
  public_ip = "X.X.X.X"
```

### Étape 4 — Attendre cloud-init (~2 min)

```bash
VM_IP=<public_ip>

# Attendre que SSH + Docker soient prêts
until ssh -o StrictHostKeyChecking=no deploy@${VM_IP} "docker info > /dev/null 2>&1"; do
  echo "Waiting..."; sleep 10
done
echo "VM ready"

ssh-keyscan -H ${VM_IP} >> ~/.ssh/known_hosts
```

### Étape 5 — Déployer l'orchestrateur

```bash
# Copier le repo
rsync -az --exclude='.git' --exclude='.venv' --exclude='__pycache__' \
  ./ deploy@${VM_IP}:~/llm-grill-nightly/

# Écrire le .env (adapter les valeurs)
ssh deploy@${VM_IP} "cat > ~/llm-grill-nightly/.env" << 'EOF'
POSTGRES_USER=llmgrill
POSTGRES_PASSWORD=changeme
ORCHESTRATOR_URL=http://<VM_IP>:8000
API_KEY=<openssl rand -hex 32>
HF_TOKEN=<ton token HF>
SCW_ACCESS_KEY=<SCW_ACCESS_KEY>
SCW_SECRET_KEY=<SCW_SECRET_KEY>
SCW_BUCKET=llmgrill-results
SCW_REGION=fr-par
GPU_ZONE=fr-par-2
DEBUG=false
EOF

# Démarrer la stack (sans Caddy)
ssh deploy@${VM_IP} "
  cd ~/llm-grill-nightly
  docker compose \
    -f docker-compose.yml \
    -f docker-compose.dev.yml \
    -f docker-compose.with-migrations.yaml \
    up --build -d postgres migration orchestrator
"
```

### Étape 6 — Vérifier

```bash
# Health check
curl http://${VM_IP}:8000/health
# → {"status":"ok"}

# Statut des containers
ssh deploy@${VM_IP} "docker compose -f ~/llm-grill-nightly/docker-compose.yml ps"

# Logs si problème
ssh deploy@${VM_IP} "docker logs llmgrill-orchestrator --tail=50"
```

### Étape 7 — Détruire

```bash
cd infra

AWS_ACCESS_KEY_ID=<SCW_ACCESS_KEY> \
AWS_SECRET_ACCESS_KEY=<SCW_SECRET_KEY> \
SCW_ACCESS_KEY=<SCW_ACCESS_KEY> \
SCW_SECRET_KEY=<SCW_SECRET_KEY> \
terraform destroy
```

---

## Test 2 — End-to-end (pipeline CI complète)

Valide la pipeline entière : provision → bench → export leaderboard → destroy.

### Prérequis

Tous les secrets GitHub suivants doivent être configurés dans `Settings → Secrets → Actions` (environment `production`) :

| Secret | Comment l'obtenir |
|---|---|
| `DEPLOY_SSH_KEY` | Clé privée ED25519 : `cat ~/.ssh/id_ed25519` |
| `DEPLOY_SSH_PUBLIC_KEY` | Clé publique correspondante : `ssh-keygen -y -f ~/.ssh/id_ed25519` |
| `POSTGRES_USER` | Ex: `llmgrill` |
| `POSTGRES_PASSWORD` | Ex: `openssl rand -hex 16` |
| `API_KEY` | `openssl rand -hex 32` |
| `HF_TOKEN` | https://huggingface.co/settings/tokens |
| `SCW_ACCESS_KEY` | Console Scaleway → IAM → API Keys |
| `SCW_SECRET_KEY` | idem |
| `SCW_BUCKET` | Nom du bucket résultats (ex: `llmgrill-results`) |
| `SCW_REGION` | `fr-par` |
| `GPU_ZONE` | `fr-par-2` |

Le bucket `llmgrill-tfstate` doit exister (voir Test 1, Étape 1).

### Lancer un test rapide (un seul modèle)

1. Aller dans **Actions → bench → Run workflow**
2. Remplir :
   - `force` : `false`
   - `model` : nom partiel d'un petit modèle de `orchestrator/models.yaml` (ex: `Qwen`)
3. Cliquer **Run workflow**

### Suivre l'exécution

```
provision  (~5 min)   terraform apply + docker compose up
bench      (variable) POST /bench → poll → export leaderboard.json
teardown   (~2 min)   terraform destroy
```

Le job `teardown` tourne **toujours**, même si `bench` échoue.

### Vérifier le résultat

```bash
# Vérifier que leaderboard.json est dans S3
AWS_ACCESS_KEY_ID=<SCW_ACCESS_KEY> \
AWS_SECRET_ACCESS_KEY=<SCW_SECRET_KEY> \
aws s3 ls s3://<SCW_BUCKET>/ \
  --endpoint-url https://s3.fr-par.scw.cloud

# Télécharger et inspecter
AWS_ACCESS_KEY_ID=<SCW_ACCESS_KEY> \
AWS_SECRET_ACCESS_KEY=<SCW_SECRET_KEY> \
aws s3 cp s3://<SCW_BUCKET>/leaderboard.json - \
  --endpoint-url https://s3.fr-par.scw.cloud | jq .
```

### Si un job échoue

| Symptôme | Où regarder |
|---|---|
| `provision` échoue sur terraform apply | Vérifier les secrets `SCW_ACCESS_KEY` / `SCW_SECRET_KEY` et que le bucket tfstate existe |
| `provision` bloque sur "Waiting for SSH" | cloud-init trop lent — augmenter le timeout dans `bench.yml` (30 itérations × 10s = 5 min) |
| `provision` bloque sur "Waiting for /health" | Logs Docker : dans le job, ajouter `ssh deploy@${VM_IP} "docker logs llmgrill-orchestrator"` |
| `bench` échoue sur "run(s) failed" | Logs du runner GPU dans l'orchestrateur |
| `teardown` échoue | La VM reste up — lancer `terraform destroy` manuellement (voir Test 1, Étape 7) |
