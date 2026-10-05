# BIMI Setup Guide

This guide covers deployment of `logo-bimi.svg` and the repository's Phase 1
validation tools. Passing these checks is **not** proof of SVG Tiny-PS conformance
or a guarantee that an email client will display the logo.

## 1. Prepare the sending domain and artwork

- Confirm that you own or are authorized to use the artwork; review `LICENSE`.
- Configure SPF and DKIM for your mail service and aligned DMARC enforcement
  (usually `p=quarantine` or `p=reject`, with `pct=100`). Check your provider's
  current BIMI requirements before changing mail authentication policies.
- Determine whether your target providers require a Verified Mark Certificate
  (VMC) or Common Mark Certificate (CMC). This checker does not validate either.

## 2. Validate the SVG locally

From the repository root, use Python 3.11:

```sh
python3.11 scripts/validate_svg.py
```

The script checks `logo-bimi.svg` for UTF-8 encoding, well-formed XML, the SVG
namespace, root `title` and `desc` elements, and at least one `path`. It retains a
strict allowlist of elements and attributes and rejects resource references,
DOCTYPE/entity declarations, scripts, styles, images, `foreignObject`, and
animation (`animate`, `set`, `animateMotion`, `animateTransform`).

Errors explain what to fix and exit nonzero. Files larger than 32 KB (32,768
bytes) receive a recommendation warning; files larger than 64 KB (65,536 bytes)
receive a concern warning. These warnings alone do not fail local structural
validation, but CI rejects files above 64 KB. Reduce unnecessary metadata and
path complexity without changing the artwork.

Also run a dedicated BIMI/SVG Tiny-PS validator and follow its export guidance.
The structural validator is intentionally restrictive and is not a complete
implementation of that standard.

## 3. Host the logo over HTTPS

Upload the validated file to a stable public URL, for example:

```text
https://example.com/branding/logo-bimi.svg
```

Configure hosting to return HTTP `200` and `Content-Type: image/svg+xml`.
Use a valid, trusted TLS certificate. Serve the file directly without redirects,
login prompts, cookies, or access restrictions. Replace the examples with your
own sending domain and hosting URL; the logo may be hosted on a different domain.

Verify the actual GET response (not just a HEAD request):

```sh
curl --fail --proto '=https' --dump-header /tmp/bimi-headers.txt \
  --output /tmp/logo-bimi.svg https://example.com/branding/logo-bimi.svg
cat /tmp/bimi-headers.txt
```

Check for HTTP `200` and the SVG content type; confirm the downloaded file is the
expected SVG, not an HTML error page. Revalidate the downloaded artifact with a
dedicated BIMI validator. Never disable TLS certificate verification to make a
check pass.

## 4. Publish the BIMI DNS record

Create one TXT record at `default._bimi` for the **sending domain**:

```text
default._bimi.example.com. TXT "v=BIMI1; l=https://example.com/branding/logo-bimi.svg;"
```

If your deployment uses a certificate, publish its public HTTPS URL in `a=`:

```text
default._bimi.example.com. TXT "v=BIMI1; l=https://example.com/branding/logo-bimi.svg; a=https://example.com/branding/mark-certificate.pem;"
```

DNS control panels often append the zone name automatically: enter
`default._bimi` in that case, not the full name twice. Publish one BIMI record,
not multiple competing TXT records. Wait for the DNS TTL and propagation.

## 5. Check DNS and hosting

Install the compliance checker's dependencies:

```sh
python3.11 -m pip install dnspython==2.8.0 requests==2.34.2
python3.11 scripts/check_bimi_compliance.py --domain example.com
```

The checker queries `default._bimi.example.com`, joins split TXT strings, checks
the `l=` HTTPS URL, tests accessibility with GET, and checks `Content-Type`.
To test hosting before DNS is ready, supply an explicit URL:

```sh
python3.11 scripts/check_bimi_compliance.py --domain example.com \
  --svg-url https://example.com/branding/logo-bimi.svg
```

Missing or invalid DNS still produces errors; an explicit URL does not bypass
DNS validation. A supplied URL differing from the DNS `l=` value is also an
error. Reports list errors and warnings; errors produce exit code `1`, while
warnings alone produce exit code `0`. A missing `a=` is a warning because
certificate requirements vary by provider.

You can independently inspect publication with:

```sh
dig TXT default._bimi.example.com
```

In GitHub, set **Settings → Secrets and variables → Actions → Variables**:

- `BIMI_DOMAIN`: your sending domain.
- `BIMI_SVG_URL` (optional): the expected HTTPS SVG URL.

The `validate.yml` workflow runs on pushes and pull requests with Python 3.11.
Structural errors and files larger than 64 KB fail CI; the compliance step is
informational (`continue-on-error`) because public DNS and hosting may not yet
be deployed or may be temporarily unavailable. Without `BIMI_DOMAIN`, it checks
`example.com` and prints a configuration warning; this is not a deployment check
for your domain.

## 6. Test email-client display

Send authenticated mail from the configured domain to test accounts at your
target providers (for example, Gmail, Yahoo, and Apple Mail). Inspect message
headers for SPF, DKIM, and DMARC alignment, then check logo display in each
provider's supported clients. Consult their current certificate, reputation,
and display requirements. Allow time for DNS propagation and provider caching.
A successful prerequisite report does not guarantee logo display.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| UTF-8 or XML error | Re-export as UTF-8; fix the indicated XML line/column and close all tags. |
| Missing namespace, title, desc, or path | Add the SVG namespace and descriptive root children; convert artwork to paths. |
| Unsupported feature or attribute | Remove scripts, styles, embedded images, animation, and references; use self-contained vector paths. |
| Size warning or CI failure | Simplify path data and remove unnecessary metadata; keep the file at or below 65,536 bytes. |
| DNS record absent or duplicated | Check the sending domain, `default._bimi` name, TXT value, competing records, TTL, and resolver access. |
| HTTP redirect, 403, or 404 | Use the final direct URL, remove authentication restrictions, and confirm the uploaded path. |
| TLS or connection failure | Check certificate validity/chain, hostname, firewall rules, and public availability. |
| Wrong Content-Type | Set hosting MIME metadata to `image/svg+xml`; ensure the response is not an HTML error page. |
| URL mismatch | Make the expected URL and DNS `l=` value identical. |
| No logo in the email client | Verify DMARC enforcement/alignment, provider eligibility, certificate requirements, reputation, and cache delays with the mail provider. |
