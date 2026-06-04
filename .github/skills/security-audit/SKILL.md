# Skill: security-audit

Name: security-audit
Description: Security-focused code review checking OWASP (Open Web Application Security Project) Top 10 vulnerabilities.

Purpose
- Provide automated, beginner-friendly security reviews that surface OWASP Top 10 issues and offer remediation guidance.

Inputs
- Repository source files (scan path or entire repo)
- Optional config: paths to include/exclude, languages, severity thresholds

Outputs
- Markdown report listing findings with severity, CWE identifiers, file/line examples, and recommended fixes
- Optional GitHub PR comments or issue creation when run with write permissions

Example usage
- copilot skill run security-audit --paths=src --format=markdown

Permissions
- Read access to repository content (required)
- Optional write access for creating PR comments/issues (opt-in)

Notes
- This skill is educational: it highlights likely issues and guidance but is not a substitute for a full security audit by professionals.
