import os
import re
from typing import Any, List

import pytest

yaml = pytest.importorskip("yaml")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", ".pre-commit-config.yaml")
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def find_unpinned_hooks(config_path: str) -> List[str]:
    """Return a description of every hook repo that is not pinned to a commit
    over https.

    Parameters
    ----------
    config_path : str
        Path to a pre-commit configuration file.

    Returns
    -------
    List[str]
        One message per offending repo; empty if every repo is pinned.
    """
    with open(config_path) as fp:
        config = yaml.safe_load(fp)
    problems = []  # type: List[str]
    for repo in config["repos"]:  # type: Any
        url = repo["repo"]
        if url in ("local", "meta"):
            continue
        if not url.startswith("https://"):
            problems.append("{} is not fetched over https".format(url))
        if "sha" in repo:
            problems.append("{} uses the deprecated `sha` key".format(url))
        rev = str(repo.get("rev", ""))
        if not COMMIT_SHA_RE.match(rev):
            problems.append("{} rev {!r} is not a full commit SHA".format(url, rev))
    return problems


def test_pre_commit_hooks_pinned_to_commit_shas_over_https() -> None:
    assert find_unpinned_hooks(CONFIG_PATH) == []


def test_find_unpinned_hooks_flags_mutable_and_insecure_sources(tmp_path: Any) -> None:
    config_path = tmp_path / ".pre-commit-config.yaml"
    config_path.write_text(
        "repos:\n"
        "-   repo: https://github.com/psf/black\n"
        "    rev: stable\n"
        "    hooks: [{id: black}]\n"
        "-   repo: git://github.com/PyCQA/pydocstyle\n"
        "    sha: master\n"
        "    hooks: [{id: pydocstyle}]\n"
        "-   repo: https://github.com/PyCQA/flake8\n"
        "    rev: cf1542cefa3e766670b2066dd75c4571d682a649\n"
        "    hooks: [{id: flake8}]\n"
        "-   repo: local\n"
        "    hooks: [{id: noop, name: noop, entry: 'true', language: system}]\n"
    )
    assert find_unpinned_hooks(str(config_path)) == [
        "https://github.com/psf/black rev 'stable' is not a full commit SHA",
        "git://github.com/PyCQA/pydocstyle is not fetched over https",
        "git://github.com/PyCQA/pydocstyle uses the deprecated `sha` key",
        "git://github.com/PyCQA/pydocstyle rev '' is not a full commit SHA",
    ]
