# Bambu Studio opening issue — local diagnostic note

User reports repeated errors opening Bambu Studio. A local macOS diagnostic report confirms Bambu Studio 02.08.04.57 aborted on 9 October 2026. The recorded stack is in macOS application registration / menu-bar initialization, before any identifiable model-loading function. This does not establish the root cause or prove that it is the exact dialog the user saw.

The foreground capture showed Codex, not the error dialog. No preferences were reset and no application was reinstalled. No external bug report has been submitted.

Workaround for this project: use the already-installed OrcaSlicer and preserve ordinary STL files independently of slicer project files. Previous Bambu command-line slicing evidence remains separate from the reported GUI opening problem.
