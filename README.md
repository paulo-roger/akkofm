# MastoFM: Mastodon + LastFM

Bateu nostalgia dos tempos de MSN Messenger e seu recurso _ouvindo agora_? Adicione a música em reprodução do seu LastFM nos metadados do seu perfil no Mastodon.

![Perfil no Mastodon com um dos campos mostrando a música sendo reproduzida no momento](https://pub.cdn.bolha.one/mastodon/img/perfil.png)

## Como usar esse script

O script `update.py` precisa acessar as seguintes variáveis de ambiente:

- `LAST_API_KEY`: API Key de uma [aplicação no LastFM](https://www.last.fm/api)
- `LAST_USER`: seu usuário no LastFM
- `MAST_ACC_TOKEN`: um _access token_ de um [app no Mastodon](https://docs.joinmastodon.org/client/token/).
    - Gere seu token facilmente preenchendo o campo 3 [neste link](https://token.bolha.one/?client_name=MastoFM&scopes=read:accounts%20write:accounts).
- `INSTANCE_URL`: a URL da instância em que o app foi criado

Ao executar `update.py` uma única vez, ele usará a API do LastFM para determinar se o usuário está reproduzindo uma música no momento. Se estiver, adiciona ou atualiza um metadado `Ouvindo agora 🔊` na conta do usuário com o token em `MAST_ACC_TOKEN`.

Para manter `Ouvindo agora 🔊` atualizado conforme você escuta um álbum ou playlist, execute `update.py` periodicamente (usando, por exemplo, um agendador como o `cron`) ou usar a imagem Docker.

> Caso sua instância seja modificada e suporte mais de 4 campos extras na bio do perfil, o script não irá funcionar pra você (por limitação do `mastodon.py`).

## Execução automática

Para manter o script rodando a cada dois minutos para saber se você está ouvindo música, use um `systemd-timer`. Caso use a imagem Docker, isto não é necessário.

Primeiro, salve o seguinte código em `/etc/systemd/system/mastofm.service`:

``` ini
[Unit]
Description=Mastodon Now Playing
After=network-online.target
Wants=mastofm.timer

[Service]
Type=simple
Environment="PYTHONUNBUFFERED=1"
Environment="LAST_API_KEY=<insira_aqui>"
Environment="LAST_USER=<insira_aqui>"
Environment="MAST_ACC_TOKEN=<insira_aqui>"
Environment="INSTANCE_URL=<insira_aqui>"
DynamicUser=yes
Restart=always
RestartSec=1 
WorkingDirectory=/opt/mastofm
ExecStart=/usr/bin/python3 /opt/mastofm/update.py
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target
```

Agora, salve o seguinte código em `/etc/systemd/system/mastofm.timer`:

``` ini
[Unit]
Description=Timer do Mastodon Now Playing

[Timer]
Unit=mastofm.service
OnCalendar=*:0/2
Persistent=true
AccuracySec=1us

[Install]
WantedBy=timers.target
```

Por fim, faça o _timer_ ser executado e passe a iniciar com o sistema:

``` bash
systemctl daemon-reload
systemctl enable --now mastofm.timer
```

O _timer_ será executado a cada dois minutos e, se você estiver ouvindo alguma coisa, o nome da música aparecerá em seu perfil. Lembre de alterar `/opt/mastofm/` pelo caminho da pasta onde o arquivo `update.py` está.

## Usando com o Docker

Use nossa nova imagem e execute o Mastodon Now Listening em um contêiner Docker.

``` bash
docker pull code.bolha.one/bolha/mastofm:latest
```

Depois de editar o arquivo `docker-compose.yml`, suba o contêiner com o comando: `docker-compose up -d`.