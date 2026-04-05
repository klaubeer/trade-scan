# Deploy TradeScan — VPS klauberfischer.online

## Pré-requisitos
- VPS com Traefik rodando em `/root/infra/`
- Rede Docker `proxy` já criada
- Domínio `tradescan.klauberfischer.online` apontando para o IP da VPS

---

## Passos

### 1. Verificar instância ativa do Traefik
```bash
docker inspect traefik | grep "com.docker.compose.project.working_dir"
```

### 2. Subir o projeto na VPS
```bash
# Na sua máquina local
scp -r . root@<IP_VPS>:/root/projetos/trade-scan

# OU via git (recomendado)
ssh root@<IP_VPS>
cd /root/projetos
git clone <repo-url> trade-scan
cd trade-scan
```

### 3. Criar o .env.prod (ANTES do primeiro up)
```bash
cp .env.prod.example .env.prod
nano .env.prod   # preencher ANTHROPIC_API_KEY
```

### 4. Subir os containers
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

### 5. Rodar o seed dos setups (primeira vez)
```bash
docker exec tradescan-backend python -m backend.banco.seed
```

### 6. Verificar logs
```bash
docker logs tradescan-backend --tail 50
docker logs tradescan-frontend --tail 20
```

---

## Atualizar depois de mudanças

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

## Mudanças no .env.prod

```bash
# restart NÃO relê o .env — sempre down + up
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

---

## Volumes persistentes
- `tradescan-dados` → `/dados/tradescan.db` (banco DuckDB)
- `tradescan-models` → `/app/models/` (modelos CNN treinados)
