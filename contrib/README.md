# contrib

Example files for running ddserver, see [Installation](../docs/installation.md).

- `systemd/ddserver.service` – gunicorn on `127.0.0.1:8080`. systemd creates
  `/var/lib/ddserver` and makes the rest of the system read-only for the service.
- `systemd/ddserver-dns-sync.service` and `.timer` – publish pending changes to
  the DNS server every five minutes.
- `caddy/Caddyfile` – HTTPS reverse proxy with an automatic certificate.
