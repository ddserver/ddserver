# Installation

ddserver in a virtual environment in `/opt/ddserver`, gunicorn as WSGI server,
Caddy for HTTPS, systemd for the services. Example files are in `contrib/`.

## Install

```sh
useradd --system --create-home --home-dir /var/lib/ddserver --shell /usr/sbin/nologin ddserver
python3 -m venv /opt/ddserver

git clone https://github.com/ddserver/ddserver /usr/local/src/ddserver
/opt/ddserver/bin/pip install '/usr/local/src/ddserver' gunicorn
```

If you migrate from ddserver 0.3 and need the old password hashes (sha512_crypt)
to keep working, run this instead:

```sh
/opt/ddserver/bin/pip install '/usr/local/src/ddserver[legacy]' gunicorn
```

pip copies ddserver into `/opt/ddserver`; the clone is only needed for updates.


## Configure

```sh
install -d -m 755 /etc/ddserver
install -m 640 -g ddserver /usr/local/src/ddserver/ddserver.example.toml \
    /etc/ddserver/ddserver.toml
```

The complete configuration resides in one TOML file, which by default is
`/etc/ddserver/ddserver.toml`. A different file can be chosen with `--config` or
by setting the `DDSERVER_CONFIG` environment variable.

See the example configuration file [`ddserver.example.toml`](../ddserver.example.toml)
for a description of all possible options. Restart ddserver after changes to the
configuration file.

Edit `/etc/ddserver/ddserver.toml`: Set at least `secret_key` and `base_url`,
the `[dns]` and `[mail]` sections, and `proxies = 1` behind Caddy. See
[DNS server setup](dns.md).

## Run commands as the user ddserver

The database belongs to the user `ddserver`. Run every `ddserver` command as this
user, otherwise file permissions will be wrong.

```sh
alias ddserver='sudo -u ddserver /opt/ddserver/bin/ddserver'
```

## Start

```sh
cp /usr/local/src/ddserver/contrib/systemd/* /etc/systemd/system/
systemctl daemon-reload

ddserver db upgrade
ddserver user add --admin USERNAME EMAIL
ddserver zone add dyn.example.org

systemctl enable --now ddserver.service ddserver-dns-sync.timer
```

Add `contrib/caddy/Caddyfile` (with your hostname) to the Caddy configuration and
reload Caddy.

## Check

- `https://ddserver.example.org/nic/ip` shows your public address. `127.0.0.1`:
  `proxies` is not set; a wrong address: `proxies` is too high.
- `ddserver mail test ADDRESS` sends a test mail.
- Logs: `journalctl -u ddserver -u ddserver-dns-sync`.

## Update

```sh
git -C /usr/local/src/ddserver pull
/opt/ddserver/bin/pip install --upgrade '/usr/local/src/ddserver' gunicorn
ddserver db upgrade
systemctl restart ddserver
```

## Command line

```
ddserver db upgrade                         create or upgrade the database
ddserver user add [--admin] USERNAME EMAIL  add an activated user
ddserver user list
ddserver user delete USERNAME
ddserver user grant-admin USERNAME
ddserver user revoke-admin USERNAME
ddserver user host-limit USERNAME LIMIT     number, default or unlimited
ddserver zone add NAME
ddserver zone list
ddserver zone delete NAME
ddserver dns sync [--all]                   publish pending changes (--all: every host)
ddserver mail test ADDRESS
ddserver run                                development server only
```

`--help` on every command shows its options.
