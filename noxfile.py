import nox

nox.options.reuse_existing_virtualenvs = True


@nox.session
def lint(session):
    """Run linters."""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files")


@nox.session
def test(session):
    """Run the test suite."""
    session.install(".")
    session.install("pytest")
    session.run("pytest")


@nox.session
def coverage(session):
    """Run the test suite with coverage."""
    session.install(".")
    session.install("pytest", "pytest-cov")
    session.run("coverage", "run", "-m", "pytest")
    session.run("coverage", "report")
    session.run("coverage", "html")
    session.run("coverage", "xml")  # Generate coverage.xml for codecov


@nox.session
def build(session):
    """Build the package."""
    session.install("build")
    session.run("python", "-m", "build")


@nox.session
def publish(session):
    """Publish the package to PyPI."""
    session.install("twine")
    session.run("twine", "check", "dist/*")
    session.run("twine", "upload", "dist/*")
