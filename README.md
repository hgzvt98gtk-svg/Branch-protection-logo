# BIMI Logo

A self-contained SVG logo prepared for use with **Brand Indicators for Message Identification (BIMI)**.

## Preview

![BIMI logo](logo-bimi.svg)

- [View the SVG](logo-bimi.svg)
- [Download the raw SVG](https://raw.githubusercontent.com/hgzvt98gtk-svg/bimi-logo/main/logo-bimi.svg)

## Purpose

This repository contains the `logo-bimi.svg` artwork intended to be hosted by a domain that publishes a BIMI record. Use the logo only when you own it or have permission from the rights holder.

## Usage

1. Confirm that you own or are authorized to use the logo.
2. Host `logo-bimi.svg` at a stable HTTPS URL on the relevant domain.
3. Publish a BIMI DNS TXT record for the sending domain.
4. Validate the hosted SVG and DNS configuration with your email provider and a BIMI validator.

Example DNS record:

```text
default._bimi.example.com TXT "v=BIMI1; l=https://example.com/path/to/logo-bimi.svg;"
```

Replace `example.com` and the SVG URL with your own domain and hosting location. Requirements can vary between receiving mail systems; BIMI may also require sender authentication and, depending on the deployment, an appropriate certificate.

## File requirements

The hosted logo should:

- Remain a self-contained SVG.
- Be served over HTTPS.
- Avoid scripts, external resources, and unsupported SVG features.
- Preserve the intended artwork and proportions.
- Be tested with a BIMI/SVG validator before publication.

Do not modify, redistribute, or use the logo commercially without permission from the rights holder.

## Automated validation

Pull requests and pushes run a structural check on `logo-bimi.svg`. It checks that the file is valid UTF-8 XML, uses the SVG namespace, contains a title, description, and path, and avoids unsupported elements, attributes, and referenced resources.

This repository check does not verify BIMI Tiny-PS conformance, hosted HTTPS availability, DNS records, sender authentication, or provider-specific requirements. Validate those separately with your email provider and a BIMI validator before deployment.

## Repository contents

| File | Description |
| --- | --- |
| [`logo-bimi.svg`](logo-bimi.svg) | BIMI logo SVG |
| [`scripts/validate_svg.py`](scripts/validate_svg.py) | Structural SVG validator used by CI |

## License and trademark

The repository includes a restrictive `LICENSE` file. It does not grant permission to copy, modify, distribute, publish, sublicense, or commercially use the logo without prior written permission. The logo may also be protected by trademark rights. Review the license and obtain permission before reuse.

## Contributing

Open an issue before proposing changes to the logo. Any proposed SVG should preserve the artwork and remain compatible with the intended BIMI use case.
