# Security Policy

PyTeaser fetches and parses content from user-supplied URLs, so the URL and
image safety rules are treated as security boundaries.

## Supported versions

Only the latest release receives security fixes.

## Reporting a vulnerability

Please report vulnerabilities privately to the maintainers via
[GitHub security advisories](https://github.com/xiaoxu193/PyTeaser/security/advisories/new).
Do not open public issues for suspected vulnerabilities.

Include a description, reproduction steps, and affected versions. You will
receive an acknowledgement within a week where possible.

## Security-relevant guarantees

- Only `http`/`https` schemes on standard ports are fetched.
- Hostnames are resolved and validated; private, loopback, link-local, and
  other non-global addresses are rejected unless explicitly overridden.
- Redirect targets are revalidated before being followed.
- Requests enforce a timeout, and HTML/image responses enforce size caps.
- Image fetching is disabled by default and requires an extra dependency.

Changes that relax these guarantees (for example `allow_private_network=True`)
must never be enabled for untrusted input.
