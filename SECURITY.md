# Security Policy

Guyline is a local coding and personal agent harness. Because it can run
commands, edit files and store provider credentials, please treat security
reports seriously and follow the process below.

## Supported Versions

Security fixes are provided for the latest released `0.2.x` line. Older or
unreleased snapshots are not supported. If you are unsure whether a version is
supported, say so in your report and we will clarify.

## Reporting a Vulnerability

Please report suspected vulnerabilities **privately**. Do not open a public
issue, pull request or discussion for an unfixed vulnerability, and do not
publish details before a fix is available.

Preferred channel: GitHub Private Vulnerability Reporting for this repository
(the repository **Security** tab → **Report a vulnerability**). If that option
is not offered for this repository, contact the maintainer privately through the
GitHub profile maintained at <https://github.com/imddn>. This document does not
list an email address; please use one of the channels above rather than guessing
one.

Please include, as far as you can:

- affected Guyline version or commit, and how it was installed;
- operating system and Python version, and the provider/auth setup involved;
- the impact you believe is possible and the conditions required;
- clear reproduction steps, and any proof-of-concept or logs with secrets,
  tokens and personal data redacted.

## What To Expect

Guyline is a small, maintainer-run project. We aim to acknowledge valid reports
and keep reporters informed as a fix progresses, but we cannot promise a fixed
response time or fix deadline. Please allow reasonable time before any public
disclosure, and coordinate timing with us so a fix can be released first.

## Scope And Sensitive Areas

Reports are especially useful in these areas:

- credential handling and storage, including `GUYLINE_*` configuration,
  provider API keys, external credential bindings, sessions, logs and memory
  files that may contain sensitive data;
- permission modes and tool execution (`bash`, file write/edit, worktrees);
- bundled or user-installed plugins, skills and MCP servers, which run
  third-party code and should be reviewed before enabling;
- chat channel and gateway endpoints that can receive untrusted input.

## Self-Hosted Runners

The autopilot workflows (`.github/workflows/autopilot-scan.yml` and
`.github/workflows/autopilot-run-next.yml`) write to the repository and run on a
**self-hosted** runner. Treat these as privileged, maintainer-only operations:

- triggering is manual (`workflow_dispatch`) and must be limited to trusted
  maintainers; never wire autopilot to run automatically;
- never point these jobs at untrusted pull-request, issue or fork content, and
  do not check out untrusted refs;
- isolate the runner workspace (dedicated or ephemeral runners are preferred)
  and clean the workspace between runs so credentials and checkout data do not
  leak between jobs;
- keep credentials minimal: grant only the repository write permissions the job
  actually needs (`contents`, `issues`, `pull-requests` as required by the
  autopilot design) and do not widen them to other jobs;
- review the write operations these jobs perform (git push and `gh` issue/PR
  actions) as you would any other privileged automation.

## No Guarantees

This policy describes how we handle reports; it is not a guarantee that Guyline
is free of vulnerabilities or that any particular issue will be fixed. Provide
your own review and access controls appropriate to your environment.
