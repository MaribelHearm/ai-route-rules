# Public AI destination rules

Three Mihomo rule providers, on the `main` branch:

| File | Contents | Maintenance |
| --- | --- | --- |
| `rules/ai.yaml` | Global AI services and their dependencies | Daily conversion of [VPSDance/ai-proxy-rules](https://github.com/VPSDance/ai-proxy-rules), `rules/sing-box/global.json` |
| `rules/payment.yaml` | Payment services | Manual |
| `rules/accounts.yaml` | Account and app-store dependencies | Manual |

Use `behavior: classical` and `format: yaml`. Match destinations in the desired
order in your own policy. These lists do not select an outbound for you.

```yaml
rule-providers:
  ai:
    type: http
    behavior: classical
    format: yaml
    url: https://testingcf.jsdelivr.net/gh/MaribelHearm/ai-route-rules@main/rules/ai.yaml
    path: ./rules/ai.yaml
    interval: 86400
```

Replace the repository slug in the example when hosting your own copy. The
workflow uses `github.repository`, so it needs no hard-coded owner. No branch
other than `main` is needed. Enable Actions with write permission after publishing.

The converter preserves exact domains, suffixes, keywords and regular expressions.
IP ranges use `IP-CIDR` / `IP-CIDR6` with `no-resolve`. Upstream process names are
intentionally excluded: this is a destination list, shared by clients and servers.
Unknown fields, invalid input, fewer than 200 destination entries, or a loss of
more than 20% relative to the current file fail before writing. The one exception
is a malformed domain or suffix: up to 5 are dropped with a workflow warning, so a
stray upstream entry does not block the whole update; more than 5 still fail. Manual providers
are not overwritten. `stripe.com` belongs to the AI provider, not the payment
provider. The global list excludes the upstream domestic AI collection; this
does not imply that all auxiliary service domains are foreign-owned.

Regular expressions are compiled with the real Go `regexp` engine before writing.
A missing Go installation or an invalid expression fails the entire update.

Run locally with Python 3.12+ and Go 1.24+:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests
python scripts/update.py
# Reproduce an archived input:
python scripts/update.py --source-file global.json
```

The daily workflow also supports manual runs, commits only changed content and
refreshes jsDelivr after publishing. Scheduled workflows in inactive public
repositories may be disabled after 60 days; a successful no-change run does not
create a keep-alive commit. Monitor workflow freshness and re-enable scheduling
when necessary. CDN propagation is asynchronous; consumers needing a consistent
snapshot should resolve `main` once, then fetch every file at that commit.

Upstream data remains subject to its [upstream license and attribution](https://github.com/VPSDance/ai-proxy-rules).
