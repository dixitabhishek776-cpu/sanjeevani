name: Security report
description: Report a suspected security vulnerability
labels: [security]
body:
  - type: markdown
    attributes:
      value: |
        Please do not include secrets or personal data. For suspected active vulnerabilities, use the private security reporting channel documented in SECURITY.md.
  - type: textarea
    id: summary
    attributes:
      label: Summary
    validations:
      required: true
  - type: textarea
    id: reproduction
    attributes:
      label: Reproduction steps
  - type: textarea
    id: impact
    attributes:
      label: Impact
