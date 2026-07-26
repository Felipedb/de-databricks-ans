#!/usr/bin/env bash
#
# Inicializa o repositório, cria a história em commits lógicos e publica no
# GitHub. Roda na SUA máquina, com a SUA credencial: nada de token em chat.
#
# Pré-requisitos:
#   git, gh (GitHub CLI) autenticado via `gh auth login`
#
# Uso:
#   chmod +x scripts/bootstrap_git.sh
#   ./scripts/bootstrap_git.sh                    # cria repo público e envia
#   ./scripts/bootstrap_git.sh --dry-run          # só mostra o que faria
#   ./scripts/bootstrap_git.sh --no-push          # commita local, não publica
#   REPO_NAME=outro-nome ./scripts/bootstrap_git.sh
#
set -euo pipefail

REPO_NAME="${REPO_NAME:-de-databricks-ans}"
VISIBILIDADE="${VISIBILIDADE:---public}"
DESCRICAO="Medalhão em Databricks: Delta Live Tables, Auto Loader, expectations e Unity Catalog sobre dados abertos da ANS"
DRY_RUN=0
PUSH=1

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --no-push) PUSH=0 ;;
    *) echo "argumento desconhecido: $arg" >&2; exit 2 ;;
  esac
done

log()  { printf '\033[36m›\033[0m %s\n' "$*"; }
erro() { printf '\033[31m✗\033[0m %s\n' "$*" >&2; exit 1; }

executar() {
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '  [dry-run] %s\n' "$*"
  else
    "$@"
  fi
}

# ---------------------------------------------------------------------------
# Verificações antes de tocar em qualquer coisa
# ---------------------------------------------------------------------------

command -v git >/dev/null || erro "git não encontrado"
[[ -f README.md && -f databricks.yml ]] || erro "rode este script da raiz do repositório"

if [[ $PUSH -eq 1 ]]; then
  command -v gh >/dev/null || erro "gh não encontrado. instale o GitHub CLI ou use --no-push"
  gh auth status >/dev/null 2>&1 || erro "gh não autenticado. rode: gh auth login"
fi

if [[ -d .git ]]; then
  erro ".git já existe aqui. apague ou rode em uma cópia limpa"
fi

# Garante que nada sensível entre na primeira leva.
if [[ -f .env ]]; then
  grep -q '^\.env$' .gitignore || erro ".env existe e não está no .gitignore"
  log ".env presente e ignorado, ok"
fi

# ---------------------------------------------------------------------------
# História em blocos lógicos
# ---------------------------------------------------------------------------

log "inicializando repositório"
executar git init -q
executar git branch -M main

commit() {
  local mensagem="$1"; shift
  local encontrou=0
  for caminho in "$@"; do
    if compgen -G "$caminho" >/dev/null 2>&1; then
      executar git add -- "$caminho"
      encontrou=1
    fi
  done
  if [[ $encontrou -eq 0 ]]; then
    printf '  aviso: nenhum arquivo para "%s", commit pulado\n' "$mensagem" >&2
    return 0
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '  [dry-run] git commit -m "%s"\n' "$mensagem"
  else
    git diff --cached --quiet && return 0
    git commit -q -m "$mensagem"
    printf '  commit: %s\n' "$mensagem"
  fi
}

log "criando commits"
commit "chore: estrutura do projeto e configuração de lint" \
  .gitignore pyproject.toml requirements-dev.txt

commit "feat(ingestao): cliente dos dados abertos da ANS com retry e extração de ZIP" \
  "src/__init__.py" "src/ingestion/__init__.py" src/ingestion/ans_client.py

commit "test(ingestao): cobertura de URL, extração e ZIP sem CSV" \
  "tests/__init__.py" tests/test_ans_client.py

commit "feat(bronze): Auto Loader sobre o volume de landing" \
  src/dlt/bronze.py

commit "feat(silver): tipagem, dedup e expectations como quality gate" \
  src/dlt/silver.py

commit "feat(gold): indicadores por operadora e competência" \
  src/dlt/gold.py

commit "feat(bundle): pipeline como código via Databricks Asset Bundles" \
  databricks.yml "resources/*"

commit "ci: lint, testes, validação do bundle e varredura de segredos" \
  ".github/workflows/*.yml"

commit "docs: README com diagrama e registro de decisões" \
  README.md "docs/*" "scripts/*"

# Rede de segurança: se sobrou arquivo fora dos blocos acima.
if [[ $DRY_RUN -eq 0 ]] && [[ -n "$(git status --porcelain)" ]]; then
  git add -A && git commit -q -m "chore: arquivos remanescentes"
  log "arquivos remanescentes commitados"
fi

# ---------------------------------------------------------------------------
# Publicação
# ---------------------------------------------------------------------------

if [[ $PUSH -eq 0 ]]; then
  log "commits criados localmente. publique quando quiser:"
  printf '    gh repo create %s %s --source=. --push\n' "$REPO_NAME" "$VISIBILIDADE"
  exit 0
fi

log "criando e publicando $REPO_NAME no GitHub"
executar gh repo create "$REPO_NAME" "$VISIBILIDADE" \
  --description "$DESCRICAO" --source=. --remote=origin --push

if [[ $DRY_RUN -eq 0 ]]; then
  executar gh repo edit "$REPO_NAME" \
    --add-topic data-engineering --add-topic databricks \
    --add-topic delta-live-tables --add-topic data-quality \
    --add-topic unity-catalog --add-topic pyspark --add-topic medallion-architecture
  log "pronto: $(gh repo view "$REPO_NAME" --json url --jq .url)"
  log "último passo manual: fixe o repositório no seu perfil (Customize your pins)"
fi
