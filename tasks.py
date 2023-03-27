"""Tasks for use with Invoke."""
import os
import sys
from distutils.util import strtobool

from invoke import task

try:
    import toml
except ImportError:
    sys.exit(
        "Please make sure to `pip install toml` or enable the Poetry shell and run `poetry install`."
    )


PYPROJECT_CONFIG = toml.load("pyproject.toml")
TOOL_CONFIG = PYPROJECT_CONFIG["tool"]["poetry"]

# Can be set to a separate Python version to be used for launching or building image
PYTHON_VER = os.getenv("INVOKE_PYNAUTOBOT_PYTHON_VER", os.getenv("PYTHON_VER", "3.8"))

# Gather current working directory for Docker commands
PWD = os.getcwd()
# Local or Docker execution provide "local" to run locally without docker execution
INVOKE_LOCAL = strtobool(os.getenv("INVOKE_LOCAL", "False"))

_DEFAULT_SERVICE = "powerdnsapi-dev"
_DOCKER_COMPOSE_ENV = {
    "COMPOSE_FILE": "development/docker-compose.yml",
    "COMPOSE_HTTP_TIMEOUT": "86400",
    "COMPOSE_PROJECT_NAME": "powerdnsapi",
    "PYTHON_VER": PYTHON_VER,
}


@task
def start(context):
    print("Starting PowerDNSAPI in detached mode...")
    return context.run("docker-compose up -d", env=_DOCKER_COMPOSE_ENV, pty=True)


@task
def stop(context):
    print("Stopping PowerDNSAPI...")
    return context.run("docker-compose stop", env=_DOCKER_COMPOSE_ENV, pty=True)


@task
def destroy(context):
    down(context, remove=True)


@task
def down(context, remove=False):
    print("Stopping PowerDNSAPI and removing resources...")
    command = [
        "docker-compose",
        "down",
        "--remove-orphans",
        "--rmi local" if remove else "",
        "--volumes" if remove else "",
    ]
    return context.run(" ".join(command), env=_DOCKER_COMPOSE_ENV, pty=True)


@task(
    help={
        "service": "Docker-compose service name to view (default: powerdnsapi)",
        "follow": "Follow logs",
        "tail": "Tail N number of lines or 'all'",
    }
)
def logs(context, service="", follow=False, tail=None):
    """View the logs of a docker-compose service."""
    command = [
        "docker-compose logs",
        "--follow" if follow else "",
        f"--tail={tail}" if tail else "",
        service if service else "",
    ]

    context.run(" ".join(command), env=_DOCKER_COMPOSE_ENV, pty=True)


@task
def debug(context):
    print("Starting PowerDNSAPI in debug mode...")
    return context.run("docker-compose up", env=_DOCKER_COMPOSE_ENV, pty=True)


def run_cmd(context, exec_cmd, local=INVOKE_LOCAL, service=_DEFAULT_SERVICE):
    """Wrapper to run the invoke task commands.

    Args:
        context ([invoke.task]): Invoke task object.
        exec_cmd ([str]): Command to run.
        local (bool): Define as `True` to execute locally
        service (str): Service to run command in if not local

    Returns:
        result (obj): Contains Invoke result from running task.
    """
    if local:
        print(f"LOCAL - Running command {exec_cmd}")
        result = context.run(exec_cmd, pty=True)
    else:
        print(f"DOCKER - Running command: {exec_cmd} service: {service}")
        result = context.run(
            f"docker-compose run --rm -- {service} {exec_cmd}",
            env=_DOCKER_COMPOSE_ENV,
            pty=True,
        )

    return result


@task
def build(context, nocache=False, service=_DEFAULT_SERVICE):
    """Build a Docker image.

    Args:
        context (obj): Used to run specific commands
        nocache (bool): Do not use cache when building the image
        service (str): Service to build
    """

    command = [
        "docker-compose build",
        "--progress=plain",
        "--no-cache" if nocache else "",
        "--",
        service,
    ]

    result = context.run(" ".join(command), env=_DOCKER_COMPOSE_ENV, pty=True)
    if result.exited != 0:
        print(f"Failed to build {service} image\nError: {result.stderr}")


@task
def clean(context, remove=True):
    """Remove the project specific image.

    Args:
        context (obj): Used to run specific commands
    """
    print("Attempting to remove all docker-compose resources")
    down(context, remove)


@task
def rebuild(context, remove=False):
    """Clean the Docker image and then rebuild without using cache.

    Args:
        context (obj): Used to run specific commands
        remove (bool): Remove docker-compose resources
    """
    clean(context, remove)
    build(context, nocache=True)


@task(aliases=("unittest",))
def pytest(context, local=INVOKE_LOCAL, label="", failfast=False, keepdb=False):
    """Run pytest for the specified name and Python version.

    Args:
        context (obj): Used to run specific commands
        local (bool): Define as `True` to execute locally
        label (str): Label to run tests for
        failfast (bool): Stop on first failure
        keepdb (bool): Keep the database between test runs, not implemented yet, argument is necessary for upstream CI tests
    """
    if keepdb:
        print("WARNING: `--keepdb` is not implemented yet, ignoring...")

    command = [
        "pytest -vv",
        "--maxfail=1" if failfast else "",
        label,
    ]
    run_cmd(context, " ".join(command), local, service="powerdnsapi-dev")


@task
def black(context, local=INVOKE_LOCAL, autoformat=False):
    """Run black to check that Python files adherence to black standards.

    Args:
        context (obj): Used to run specific commands
        local (bool): Define as `True` to execute locally
        autoformat (bool): Autoformat the code
    """
    exec_cmd = "black ." if autoformat else "black --check --diff ."
    run_cmd(context, exec_cmd, local)


@task
def ruff(context, local=INVOKE_LOCAL):
    """Run ruff for the specified name and Python version.

    Args:
        context (obj): Used to run specific commands
        local (bool): Define as `True` to execute locally
    """
    # pty is set to true to properly run the docker commands due to the invocation process of docker
    # https://docs.pyinvoke.org/en/latest/api/runners.html - Search for pty for more information
    exec_cmd = "ruff powerdnsapi"
    run_cmd(context, exec_cmd, local)


@task
def mypy(context, local=INVOKE_LOCAL):
    """Run mypy for the specified name and Python version.

    Args:
        context (obj): Used to run specific commands
        local (bool): Define as `True` to execute locally
    """
    exec_cmd = "mypy powerdnsapi"
    run_cmd(context, exec_cmd, local)


@task
def yamllint(context, local=INVOKE_LOCAL):
    """Run yamllint to validate formatting adheres to NTC defined YAML standards.

    Args:
        context (obj): Used to run specific commands
        local (bool): Define as `True` to execute locally
    """
    exec_cmd = "yamllint ."
    run_cmd(context, exec_cmd, local)


@task
def bandit(context, local=INVOKE_LOCAL):
    """Run bandit to validate basic static code security analysis.

    Args:
        context (obj): Used to run specific commands
        local (bool): Define as `True` to execute locally
    """
    exec_cmd = "bandit --recursive ./ --configfile .bandit.yml"
    run_cmd(context, exec_cmd, local)


@task
def cli(context):
    """Enter the image to perform troubleshooting or dev work.

    Args:
        context (obj): Used to run specific commands
    """
    run_cmd(context, "bash", False)


@task
def tests(context, local=INVOKE_LOCAL):
    """Run all tests for the specified name and Python version.

    Args:
        context (obj): Used to run specific commands
        local (bool): Define as `True` to execute locally
    """
    black(context, local)
    ruff(context, local)
    mypy(context, local)
    yamllint(context, local)
    # Skipping due to using different doc strings atm.
    # pydocstyle(context, local)
    bandit(context, local)
    # Skipping due to lack of testing
    # pytest(context, local)

    print("All tests have passed!")


@task
def export(context):
    """Export compose configuration to `compose.yaml` file."""
    context.run(
        "docker-compose convert > compose.yaml", env=_DOCKER_COMPOSE_ENV, pty=True
    )