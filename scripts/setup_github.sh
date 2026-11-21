#!/usr/bin/env bash
# Crea el repositorio en GitHub, sube el código, invita al equipo y deja listos labels, milestones e issues.
#
#   gh auth login                      # una sola vez
#   scripts/setup_github.sh MI_USUARIO/plataforma-salas [--public] -- usuario2 usuario3 usuario4
#
# Requiere: git y gh (https://cli.github.com). Es seguro volver a correrlo: lo que ya existe se omite.
set -euo pipefail

REPO="${1:?Uso: $0 OWNER/REPO [--public] [-- colaborador1 colaborador2 ...]}"; shift
VIS="--private"; COLABS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --public) VIS="--public" ;;
    --) shift; COLABS=("$@"); break ;;
  esac; shift
done
cd "$(dirname "$0")/.."
gh auth status >/dev/null || { echo "Primero: gh auth login"; exit 1; }

# 1. Repositorio + push
if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "• El repo $REPO ya existe"
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$REPO.git"
else
  gh repo create "$REPO" $VIS --description "Plataforma de asignación de salas y reportes QR · Taller de Proyectos Tecnológicos" --source . --remote origin
fi
git push -u origin main

# 2. Opciones de merge: solo squash, borrar ramas
gh repo edit "$REPO" --enable-squash-merge --enable-merge-commit=false --enable-rebase-merge=false --delete-branch-on-merge || true

# 3. Colaboradores (reciben una invitación por correo)
for u in "${COLABS[@]:-}"; do
  [ -n "$u" ] && gh api -X PUT "repos/$REPO/collaborators/$u" -f permission=push >/dev/null && echo "• Invitado: $u"
done

# 4. Labels
mk_label() { gh label create "$1" --color "$2" --description "$3" --repo "$REPO" --force >/dev/null; }
mk_label must     B60205 "Must have del PMV (CA-01, 02, 05, 06)"
mk_label should   D93F0B "Should have"
mk_label could    FBCA04 "Could have"
mk_label B1       1D76DB "Bloque 1 · Datos"
mk_label B2       5319E7 "Bloque 2 · Motor de optimización"
mk_label B3       0E8A16 "Bloque 3 · Backend e interfaz web"
mk_label B4       006B75 "Bloque 4 · Reportes QR y soporte"
mk_label atp      C5DEF5 "Proceso de aceptación"
mk_label datos    BFD4F2 "Datos / planillas"
mk_label infra    EDEDED "Infraestructura y despliegue"

# 5. Milestones (la API los crea; si ya existen, falla en silencio)
for m in "1 · PMV (motor y panel)" "2 · Datos y ATP" "3 · Aceptación (ATP)" "4 · Producción"; do
  gh api "repos/$REPO/milestones" -f title="$m" >/dev/null 2>&1 || true
done

# 6. Issues desde docs/backlog.tsv (no duplica los que ya tienen ese título)
EXISTENTES="$(gh issue list --repo "$REPO" --state all --limit 500 --json title --jq '.[].title')"
while IFS='|' read -r titulo labels milestone cuerpo; do
  [ -z "$titulo" ] && continue
  if grep -Fxq "$titulo" <<<"$EXISTENTES"; then echo "• ya existe: $titulo"; continue; fi
  gh issue create --repo "$REPO" --title "$titulo" --label "$labels" --milestone "$milestone" --body "$cuerpo" >/dev/null && echo "+ $titulo"
done < docs/backlog.tsv

# 7. Protección de main (en repos privados con plan gratuito GitHub la rechaza: se informa y se sigue)
if gh api -X PUT "repos/$REPO/branches/main/protection" --input - >/dev/null 2>&1 <<'JSON'
{"required_status_checks":{"strict":true,"contexts":["pruebas"]},
 "enforce_admins":false,
 "required_pull_request_reviews":{"required_approving_review_count":1},
 "restrictions":null}
JSON
then echo "• main protegida: PR + 1 aprobación + CI verde"
else echo "! No se pudo proteger main (¿plan gratuito en repo privado?). Actívalo a mano: Settings → Branches, o hagan el repo público."; fi

echo "Listo: https://github.com/$REPO"
