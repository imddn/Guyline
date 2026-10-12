# Guyline 0.2.0

The package, Python module and sole console script are now `guyline`.
Root starts the coding CLI, `guyline agent` starts the personal Agent, and
`guyline gateway` manages run/start/stop/restart/status.

Install from a local checkout or wheel using [README](README.md). All three
installers accept source/wheel paths, discover installed frontend resources and
verify the selected interpreter and launcher. Terminal resources include an npm
lockfile, use GUYLINEJSON, and scripted input waits for backend readiness.

Configuration uses GUYLINE variables and `.guyline` directories. Legacy
directories and variables are not read or copied. Explicit paths do not import unrelated
default trees. Coding and personal memory remain separate. Credentials are
denied in every permission mode, including linked paths and custom roots.

Dashboard snapshots contain consistent sample paths. Product assets are included
consistently across the package, and genuine third-party provenance and licenses
are retained. Native Windows path coverage targets Windows Python 3.10/3.11 in
CI; Linux tests alone do not establish native Windows acceptance.
