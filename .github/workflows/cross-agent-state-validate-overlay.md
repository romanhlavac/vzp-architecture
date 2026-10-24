The existing workflow .github/workflows/cross-agent-state-validate.yml already runs:

    python -m unittest discover -s tests -v

After adding tests/test_auto_sync.py to the repo, it will discover these tests automatically.
No new GH Actions permissions, secrets, or workflow changes are needed.
