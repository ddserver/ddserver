# Update clients

Clients use the dyndns2 protocol to update their domain names. 
Login with your **username** and the **password of
the hostname** (not your account password), via HTTP Basic auth.

## Request

```
GET https://ddserver.example.org/nic/update?hostname=HOSTNAME&myip=ADDRESS
```

- `hostname` – full name, e.g. `myhost.dyn.example.org`. Up to 20, separated
  by commas, if they share the password.
- `myip` – IPv4, IPv6, or both separated by a comma. Without `myip`, the address
  of the request is used. An address of the other protocol which is not sent
  stays unchanged.

`https://ddserver.example.org/nic/ip` returns your current address.

## Answers

One line per hostname:

| Answer | Meaning |
|---|---|
| `good ADDRESS` | Changed. |
| `nochg ADDRESS` | Address was already set. |
| `badauth` | Missing login, wrong password, or account not active. |
| `nohost` | Unknown hostname or username. |
| `badagent` | Invalid `myip`. |
| `numhost` | More than 20 hostnames. |
| `911` | Server error, try again later. |

After `badauth`, `nohost` or `badagent`, fix the settings before trying again.

## Examples

Some examples of how a client can send updates.

### Curl

Install curl and use the following command.

```sh
curl -u 'USERNAME:HOSTPASSWORD' \
  'https://ddserver.example.org/nic/update?hostname=myhost.dyn.example.org&myip=192.0.2.1'
```

### ddclient

Install ddclient and use the following configuration.

```ini
protocol=dyndns2
ssl=yes
server=ddserver.example.org
login=USERNAME
password='HOSTPASSWORD'
usev4=webv4, webv4=https://ddserver.example.org/nic/ip
myhost.dyn.example.org
```

## Routers

Choose "dyndns2", "DynDNS" or a custom provider with:

- Server: `ddserver.example.org`
- Update URL, if asked for:
  `https://ddserver.example.org/nic/update?hostname=<domain>&myip=<ipaddr>,<ip6addr>`
  (placeholder names differ by router)
- Your username, and the password of the hostname

Credentials in the URL (`?username=...&password=...`) do not work; only HTTP
Basic auth does.
