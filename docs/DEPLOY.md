# Deploy — frontend na Vercel e backend na Oracle Cloud

```text
Navegador ──HTTPS──> Vercel (React, frontend/)
    │
    └──HTTPS──> VM da Oracle Cloud: Caddy (HTTPS) ──> uvicorn/FastAPI (backend/) ──> Gemini e OCI Object Storage
```

- **Frontend:** site estático na Vercel. Ele sabe onde está a API pela variável `VITE_API_URL`.
- **Backend:** uma VM *Always Free* da Oracle com Ubuntu.
  - O **Caddy** cria o certificado HTTPS sozinho, usando o endereço gratuito `IP-com-traços.sslip.io`. Não precisa comprar domínio.
  - A API só aceita o frontend listado em `CORS_ORIGINS`.

A ordem importa, porque cada lado precisa do endereço do outro:

1. Criar a VM e anotar o **IP público**.
2. Publicar o frontend na Vercel, apontando para `https://IP-com-traços.sslip.io`.
3. Instalar o backend na VM, informando o endereço da Vercel.

---

## Parte 1 — Criar a VM na Oracle Cloud

1. No Console da OCI, vá em **Compute → Instances → Create instance**.
2. **Name:** `communitylab-api`.
3. **Image:** clique em *Change image* e escolha **Canonical Ubuntu 24.04**.
4. **Shape:** clique em *Change shape* e escolha uma das opções (as duas são *Always Free*):
   - **Ampere → VM.Standard.A1.Flex**, com 1 OCPU e 6 GB. É a recomendada.
   - Se não houver capacidade, use **VM.Standard.E2.1.Micro** (1 GB). O script cria memória extra (swap).
5. **Networking:** deixe *Create new virtual cloud network* e *Create new public subnet*, com **Assign a public IPv4 address** marcado.
6. **Add SSH keys:** escolha *Generate a key pair for me* e clique em **Save private key**. Guarde o arquivo, por exemplo em `C:\Users\coutf\.ssh\oci-communitylab.key`.
7. Clique em **Create**. Quando ficar *Running*, anote o **Public IP address**, por exemplo `129.151.10.20`.

### Liberar as portas 80 e 443
1. Na página da instância, clique na **Subnet** e depois na **Security List** (*Default Security List…*).
2. Clique em **Add Ingress Rules** e crie duas regras:
   - Source CIDR `0.0.0.0/0`, IP Protocol **TCP**, Destination Port Range **80**.
   - Source CIDR `0.0.0.0/0`, IP Protocol **TCP**, Destination Port Range **443**.

O firewall interno da VM (iptables) é liberado pelo script da Parte 3.

### O endereço da API
Troque os pontos do IP por traços e acrescente `.sslip.io`:

| IP público | Endereço da API |
|---|---|
| `129.151.10.20` | `https://129-151-10-20.sslip.io` |

---

## Parte 2 — Frontend na Vercel

> A Vercel publica a branch **`main`**. Antes deste passo, faça o PR de release **`develop → main`** no GitHub, para a `main` ter o código React. A alternativa é mudar a branch em *Settings → Git → Production Branch* para `develop`.

1. Entre em **vercel.com** com a conta do GitHub e clique em **Add New → Project**.
2. Importe o repositório **MotorInteligente-G10**.
3. Configure:
   - **Root Directory:** `frontend` (clique em *Edit* e selecione a pasta).
   - **Framework Preset:** Vite (a Vercel detecta sozinha).
   - **Environment Variables:** `VITE_API_URL` = `https://129-151-10-20.sslip.io`, com o seu IP e sem barra no final.
4. Clique em **Deploy**. No fim, anote o endereço, por exemplo `https://motor-inteligente-g10.vercel.app`.

O `VITE_API_URL` é gravado no momento do build. Se você mudar a variável depois, é preciso fazer um novo deploy: aba **Deployments → ⋯ → Redeploy**.

---

## Parte 3 — Backend na VM

### 3.1 Entrar na VM (PowerShell, no seu computador)
```powershell
# Uma vez só: o SSH do Windows exige que só você leia a chave
icacls "C:\Users\coutf\.ssh\oci-communitylab.key" /inheritance:r /grant:r "$($env:USERNAME):R"

ssh -i "C:\Users\coutf\.ssh\oci-communitylab.key" ubuntu@129.151.10.20
```

### 3.2 Baixar o projeto (dentro da VM)
```bash
git clone https://github.com/Coutfernandes/MotorInteligente-G10.git
cd MotorInteligente-G10
git checkout main     # ou develop
```

### 3.3 Enviar as credenciais (num **segundo** PowerShell, no seu computador, na pasta do projeto)
```powershell
cd C:\Users\coutf\MotorInteligente-G10
scp -i "C:\Users\coutf\.ssh\oci-communitylab.key" .env oci_api_key.pem ubuntu@129.151.10.20:~/MotorInteligente-G10/
```
O `.env` e a chave **não estão no GitHub**, por isso vão por `scp`, direto do seu computador para a VM.

### 3.4 Instalar (de volta na VM)
```bash
bash backend/deploy/instalar.sh 129.151.10.20 https://motor-inteligente-g10.vercel.app
```

O script leva alguns minutos e faz:
1. Instala Python, Git e Caddy.
2. Cria 2 GB de swap.
3. Cria o `.venv` e instala as dependências.
4. Grava `CORS_ORIGINS` no `.env` com o endereço da Vercel.
5. Cria o serviço `communitylab`, que liga sozinho e reinicia se cair.
6. Configura o HTTPS e libera as portas 80 e 443 no firewall da VM.

### 3.5 Conferir
```bash
curl https://129-151-10-20.sslip.io/api/status
cd backend && ../.venv/bin/python scripts/verificar_oci.py
```
O primeiro comando deve responder com `"configurado":true` para o Gemini e para a OCI. O segundo verifica a OCI: envia um arquivo de teste e apaga em seguida.

Depois, abra o endereço da Vercel. No rodapé do menu, os dois pontos devem estar **verdes**.

---

## Atualizar depois de um novo merge
```bash
cd ~/MotorInteligente-G10
git pull
.venv/bin/pip install -r backend/requirements.txt
sudo systemctl restart communitylab
```
A Vercel publica o frontend sozinha a cada merge na branch configurada.

## Comandos úteis na VM
| Para | Comando |
|---|---|
| Ver os logs da API ao vivo | `journalctl -u communitylab -f` |
| Ver se a API está rodando | `systemctl status communitylab` |
| Reiniciar a API (depois de mudar o `.env`) | `sudo systemctl restart communitylab` |
| Ver os logs do HTTPS (Caddy) | `journalctl -u caddy -f` |
| Pacotes gerados | `ls ~/MotorInteligente-G10/data/saida/` |

## Problemas comuns
| Sintoma | Causa provável |
|---|---|
| `curl` não conecta (timeout) | Faltam as regras 80/443 na **Security List** (Parte 1) |
| Caddy falha ao obter o certificado | Porta 80 bloqueada, ou limite do Let's Encrypt para `sslip.io`. Espere alguns minutos e rode `sudo systemctl restart caddy` |
| Na Vercel, "API indisponível" ou erro de CORS no console do navegador | `CORS_ORIGINS` no `.env` da VM diferente do endereço exato da Vercel (com `https://` e sem barra final). Corrija e reinicie a API |
| Na Vercel, a interface chama `localhost` | `VITE_API_URL` não estava definido no build. Defina e faça **Redeploy** |
| OCI "Não configurado" na VM | Faltou copiar o `oci_api_key.pem` ou o `.env` (passo 3.3) |
| Instalação parou na VM de 1 GB | Rode o `instalar.sh` de novo; o swap já criado ajuda |

## Segurança
- A API fica **pública** e não tem login: quem tiver o endereço pode processar arquivos (gastando a cota do Gemini) e aprovar conteúdos. Isso serve para a demonstração do hackathon. Depois da apresentação, pare a VM (**Instance → Stop**) ou adicione autenticação.
- Nunca coloque o `.env` ou a chave `.pem` no GitHub nem nas variáveis da Vercel. O frontend não precisa de nenhuma chave.
