#!/usr/bin/env python3
"""Check public BIMI DNS and SVG hosting prerequisites, not full certification."""

import argparse
import re
from urllib.parse import urlsplit

import dns.exception
import dns.resolver
import requests


def check_https(url, errors):
    try:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("an absolute HTTPS URL is required")
        if parsed.username is not None or parsed.password is not None or parsed.fragment:
            raise ValueError("credentials and fragments are not allowed")
        parsed.port
    except ValueError as error:
        errors.append(f"Invalid SVG URL {url!r}: {error}; publish a public HTTPS URL.")
        return False
    return True


def check_compliance(domain, svg_url=None):
    errors = []
    warnings = [
        "These checks do not verify SVG Tiny-PS conformance, SPF/DKIM/DMARC, "
        "certificate eligibility, or mailbox-provider acceptance."
    ]
    domain = domain.rstrip(".")
    labels = domain.split(".")
    if len(domain) > 253 or len(labels) < 2 or any(
        not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
        for label in labels
    ):
        errors.append("Invalid sending domain; use a DNS domain such as example.com, not a URL.")
        return errors, warnings

    record_name = f"default._bimi.{domain}"
    logo_url = None
    try:
        answers = dns.resolver.resolve(f"{record_name}.", "TXT", lifetime=10)
        records = [
            b"".join(answer.strings).decode("utf-8")
            for answer in answers
        ]
        bimi_records = [
            record for record in records
            if re.match(r"^\s*v\s*=\s*BIMI1\s*(?:;|$)", record)
        ]
        if len(bimi_records) != 1:
            errors.append(
                f"{record_name} must publish exactly one BIMI TXT record; "
                f"found {len(bimi_records)}. Use v=BIMI1; l=https://example.com/logo-bimi.svg;."
            )
        else:
            tags = {}
            for part in bimi_records[0].split(";"):
                if not part.strip():
                    continue
                key, separator, value = part.strip().partition("=")
                key, value = key.strip(), value.strip()
                if not separator or not key or key in tags:
                    errors.append(f"Malformed or duplicate BIMI tag {part!r}; correct {record_name}.")
                    continue
                tags[key] = value
            logo_url = tags.get("l")
            if not logo_url:
                errors.append(f"{record_name} has no nonempty l= logo URL; add an HTTPS SVG location.")
            elif svg_url and svg_url != logo_url:
                check_https(logo_url, errors)
            if not tags.get("a"):
                warnings.append("No a= certificate URL is published; some providers require a VMC or CMC.")
    except (dns.exception.DNSException, UnicodeDecodeError) as error:
        errors.append(
            f"Cannot read TXT records at {record_name}: {error}. "
            "Check DNS publication, propagation, and resolver connectivity."
        )

    if svg_url and logo_url and svg_url != logo_url:
        errors.append(
            f"Requested SVG URL differs from the DNS l= URL ({logo_url}); "
            "update DNS or check the published URL."
        )
    target_url = svg_url or logo_url
    if target_url and check_https(target_url, errors):
        try:
            with requests.get(
                target_url,
                timeout=10,
                allow_redirects=False,
                stream=True,
                headers={"Accept": "image/svg+xml"},
            ) as response:
                if response.status_code != 200:
                    errors.append(
                        f"SVG URL returned HTTP {response.status_code}; serve the SVG directly "
                        "with HTTP 200, without authentication or redirects."
                    )
                content_type = response.headers.get("Content-Type", "")
                if content_type.split(";", 1)[0].strip().lower() != "image/svg+xml":
                    errors.append(
                        f"SVG Content-Type is {content_type!r}; configure hosting to return image/svg+xml."
                    )
        except requests.RequestException as error:
            errors.append(
                f"Cannot access SVG URL: {error}. Check public access, connectivity, "
                "and the HTTPS certificate chain."
            )
    elif not target_url:
        errors.append("No SVG URL available; publish an l= URL or supply --svg-url to test hosting.")
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", required=True, help="Sending domain, for example example.com")
    parser.add_argument("--svg-url", help="Optional HTTPS logo URL; defaults to the DNS l= value")
    args = parser.parse_args()
    errors, warnings = check_compliance(args.domain, args.svg_url)
    print(f"BIMI compliance report for {args.domain}")
    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    print(f"Result: {'FAIL' if errors else 'PASS (prerequisite checks only)'}; "
          f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
