# Releasing ff-iii-luciferin

1. Merge normal changes into `main`. `prepare-release.yml` uses Conventional
   Commits to calculate the next version and opens a `release/vX.Y.Z` pull
   request containing the Commitizen version bump, changelog, and lock file.
   The release PR's CI is dispatched explicitly because GitHub Actions does
   not automatically run PR workflows for a PR created with `GITHUB_TOKEN`.
2. Review the release PR and **squash merge** it after CI passes. The squash
   commit should retain the `bump: version ...` title. The workflow tags that
   commit and creates a **draft** GitHub Release with notes from `CHANGELOG.md`.
3. Optionally run the `Release` workflow manually with the new tag to publish
   a test build to TestPyPI. Only TestPyPI is available from manual runs.
4. Publish the draft GitHub Release when ready. The `published` event runs
   lint, tests, version and index checks, then publishes the verified wheel
   and source distribution to PyPI.

The publishing jobs continue to use the repository secrets `PYPI_API_TOKEN`
and `TEST_PYPI_API_TOKEN`. Publishing an existing version is blocked before
upload. Pushing a tag alone no longer publishes a package.
