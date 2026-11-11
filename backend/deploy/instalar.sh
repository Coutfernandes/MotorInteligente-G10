#!/usr/bin/env bash
# Instala o backend do CommunityLab numa VM Ubuntu 24.04 da Oracle Cloud (Always Free).
#
# Uso (dentro da VM, na pasta do projeto já clonado):
#   bash backend/deploy/instalar.sh <IP-PUBLICO-DA-VM> <URL-DO-FRONTEND-NA-VERCEL>
# Exemplo:
#   bash backend/deploy/instalar.sh 129.151.10.20 https://communitylab-g10.vercel.app
#
# Antes de rodar: copie o .env e o oci_api_key.pem para a raiz do projeto (veja docs/DEPLOY.md).
set -euo pipefail

IP="${1:?Informe o IP público da VM. Ex.: bash backend/deploy/instalar.sh 129.151.10.20 https://seu-app.vercel.app}"
FRONTEND="${2:?Informe a URL do frontend na Vercel. Ex.: https://seu-app.vercel.app}"
FRONTEND="${FRONTEND%/}"

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
DOMINIO="${IP//./-}.sslip.io"   # 129.151.10.20 -> 129-151-10-20.sslip.io (HTTPS sem comprar domínio)
USUARIO="$(whoami)"

echo "==> Projeto em: $RAIZ"
echo "==> Endereço da API: https://$DOMINIO"

[ -f "$RAIZ/.env" ] || { echo "ERRO: falta o arquivo $RAIZ/.env"; exit 1; }
[ -f "$RAIZ/oci_api_key.pem" ] || echo "AVISO: oci_api_key.pem não encontrado; o envio ao bucket vai falhar."

echo "==> 1/6 Pacotes do sistema (Python, Caddy para HTTPS)"
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip git caddy

echo "==> 2/6 Memória extra (swap de 2 GB), útil na VM de 1 GB"
if ! swapon --show | grep -q /swapfile; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab > /dev/null
fi

echo "==> 3/6 Ambiente Python e dependências"
python3 -m venv "$RAIZ/.venv"
"$RAIZ/.venv/bin/pip" install --upgrade pip
"$RAIZ/.venv/bin/pip" install -r "$RAIZ/backend/requirements.txt"

echo "==> 4/6 Libera o frontend da Vercel no .env (CORS)"
if grep -q '^CORS_ORIGINS=' "$RAIZ/.env"; then
  sed -i "s#^CORS_ORIGINS=.*#CORS_ORIGINS=$FRONTEND#" "$RAIZ/.env"
else
  printf '\nCORS_ORIGINS=%s\n' "$FRONTEND" >> "$RAIZ/.env"
fi
sed -i 's#^LLM_PROVIDER=simulado#LLM_PROVIDER=gemini#' "$RAIZ/.env"
chmod 600 "$RAIZ/.env" "$RAIZ/oci_api_key.pem" 2>/dev/null || true

echo "==> 5/6 Serviço da API (liga sozinho e reinicia se cair)"
sed -e "s#__RAIZ__#$RAIZ#g" -e "s#__USUARIO__#$USUARIO#g" \
  "$RAIZ/backend/deploy/communitylab.service" | sudo tee /etc/systemd/system/communitylab.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now communitylab
sudo systemctl restart communitylab

echo "==> 6/6 HTTPS com Caddy + firewall da VM (portas 80 e 443)"
sed "s#__DOMINIO__#$DOMINIO#g" "$RAIZ/backend/deploy/Caddyfile" | sudo tee /etc/caddy/Caddyfile > /dev/null
# As imagens Ubuntu da Oracle bloqueiam portas no iptables da própria VM, além da Security List.
# A liberação entra ANTES da regra REJECT que vem na imagem.
for porta in 80 443; do
  if ! sudo iptables -C INPUT -p tcp --dport "$porta" -m state --state NEW -j ACCEPT 2>/dev/null; then
    linha_reject="$(sudo iptables -L INPUT --line-numbers -n | awk '/REJECT/ {print $1; exit}')"
    if [ -n "$linha_reject" ]; then
      sudo iptables -I INPUT "$linha_reject" -p tcp --dport "$porta" -m state --state NEW -j ACCEPT
    else
      sudo iptables -A INPUT -p tcp --dport "$porta" -m state --state NEW -j ACCEPT
    fi
  fi
done
command -v netfilter-persistent > /dev/null || sudo DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent
sudo netfilter-persistent save
sudo systemctl restart caddy

echo
echo "Pronto. Teste em alguns segundos:"
echo "  curl https://$DOMINIO/api/status"
echo
echo "Na Vercel, use:  VITE_API_URL=https://$DOMINIO"
