# Installation

ddserver in a virtual environment in `/opt/ddserver`, gunicorn as WSGI server,
Caddy for HTTPS and systemd for the services. 

## Install

```sh
useradd --system --create-home --home-dir /var/lib/ddserver --shell /usr/sbin/nologin ddserver
python3 -m venv /opt/ddserver

git clone -b rewrite https://github.com/ddserver/ddserver /usr/local/src/ddserver
/opt/ddserver/bin/pip install '/usr/local/src/ddserver[legacy]' gunicorn
```


## Configure

```sh
install -d -m 755 /etc/ddserver
install -m 640 -g ddserver /usr/local/src/ddserver/ddserver.example.toml \
    /etc/ddserver/ddserver.toml
```

Edit `/etc/ddserver/ddserver.toml`.

## Run commands as the user ddserver

The database belongs to the user `ddserver`. Run every `ddserver` command as 
user ddserver.

```sh
alias ddserver='sudo -u ddserver /opt/ddserver/bin/ddserver'
```

## Start

```sh
cp /usr/local/src/ddserver/contrib/systemd/* /etc/systemd/system/
systemctl daemon-reload

ddserver db upgrade
ddserver user add --admin USERNAME EMAIL

systemctl enable --now ddserver.service ddserver-dns-sync.timer
```

Then add `caddy/Caddyfile` (with your hostname) to the configuration of Caddy and
reload it.

## Check

- `https://ddserver.example.org/nic/ip` shows your own public address. If it
  shows `127.0.0.1`, `proxies` is not set; if it shows a wrong address, it is set
  too high.
- `ddserver mail test ADDRESS` sends a test mail.
