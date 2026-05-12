# Roadmap

## Décisions actées

- **`llm-grill`** : PyPI, `aggregate()` + `RequestMetrics` stables
- **Domaine** : `llm-grill.fr` (GitHub Pages + CNAME)
- **Alerting** : email GitHub uniquement
- **`run_id`** : `YYYY-MM-DD-{git-sha}`

---

## État des vagues

### ✅ Vague 0 — Storage foundation
PR #1 mergée (`51c7677`).
- `results/` layout, fixtures JSONL, `docs/schemas.md`

### ✅ Vague 0.5 — Backend orchestrateur
Branche `feat/backend` — PR à ouvrir.
- FastAPI : runs, nodes, results, leaderboard
- Infra : terraform (Scaleway), watcher HuggingFace, storage S3
- Architecture : routers → controllers → services → repositories

### ✅ Vague 1A — Pipeline simplifié
Branche `feat/backend` (à merger).
- `models.yaml` — liste hardcodée, source de vérité
- `scripts/bench.py` — diff vs results/, POST à l'orchestrateur
- `scripts/wait_for_runs.py` — polling orchestrateur + download JSONL
- `.github/workflows/bench.yml` — trigger sur push `models.yaml` + dispatch manuel

**Décision actée** : pas de découverte HF automatique. Ajouter un modèle = PR sur `models.yaml`.

### ⏳ Vague 1B — Frontend (Sonnet)
Démarre après merge `feat/backend`, parallèle à 1A.
- SvelteKit + adapter-static sur `llm-grill.fr`
- **Une seule page** : scatter plot interactif (X/Y configurables), filtres brand/catégorie/modèle
- Données : JSON statique hardcodé dans le repo (pas de run nightly)
- `.github/workflows/deploy.yml`

**Décision actée** : pas de routes `/model/[slug]` ni `/history` pour l'instant.

### 🔒 Vague 2 — Infra Terraform (Sonnet)
Bloquée — inputs Scaleway requis : région, Project ID, IAM key, type instance, image base.
- `infra/main.tf`, `variables.tf`, `outputs.tf`
- `setup-vllm.sh`, `setup-llamacpp.sh` (cloud-init)

### 📝 001g — Runbook secrets
`docs/runbooks/secrets.md` — rédigé par l'orchestrateur en fin de Vague 2.

---

## Déploiement VM backend

### Stack

| Composant | Choix | Raison |
|-----------|-------|--------|
| Provider | Scaleway (même compte que les GPU nodes) | IAM unifié, réseau privé possible |
| Instance | DEV1-M ou PLAY2-MICRO (2 vCPU, 4 GB RAM) | Orchestrateur léger, pas de calcul |
| OS | Ubuntu 24.04 LTS | Image standard Scaleway |
| Runtime | Docker + Docker Compose | Isolation, restart automatique |
| DB | PostgreSQL 16 (container, volume persistant) | Données reconstructibles depuis S3, managé inutile ici |
| Reverse proxy | Caddy | TLS automatique Let's Encrypt, config minimale |
| Domaine | `api.llm-grill.fr` | Appelé par les GPU nodes pour les callbacks |

### Compose cible (`docker-compose.yml`)

```
orchestrator  ← FastAPI + uvicorn
postgres      ← PostgreSQL 16, volume nommé
caddy         ← reverse proxy TLS sur api.llm-grill.fr
```

### Variables d'environnement requises

```
DATABASE_URL          postgresql+asyncpg://postgres:<pwd>@postgres/llmgrill
ORCHESTRATOR_URL      https://api.llm-grill.fr
HF_TOKEN              <huggingface token>
SCW_ACCESS_KEY        <scaleway IAM key>
SCW_SECRET_KEY        <scaleway IAM secret>
SCW_BUCKET            llmgrill-results
SCW_REGION            fr-par
GPU_ZONE              fr-par-2
```

### Fichiers à créer (agent ou manuellement)

- `deploy/docker-compose.yml`
- `deploy/Caddyfile`
- `deploy/.env.example`
- `orchestrator/Dockerfile`

### À décider

- [ ] Scaleway Project ID pour la VM backend (même project que GPU nodes ?)
- [ ] DNS `api.llm-grill.fr` → IP publique de la VM (entrée A à créer)
- [ ] Backup PostgreSQL : dump quotidien vers le bucket S3 ou pas nécessaire ?

---

## Prochaine action

1. Ouvrir PR `feat/backend`
2. Brief Vague 1B (frontend) → agent Sonnet
3. Brief Vague 1A (pipeline) → agent Opus (parallèle à 1B)
4. Fournir inputs Scaleway → débloquer Vague 2
