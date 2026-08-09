import subprocess
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from bac_generator.api.routes.exercises import get_code_validator
from bac_generator.core.config import settings
from bac_generator.core.exceptions import CodeCompilationError
from bac_generator.services.local_code_runner import LocalCodeRunner
from bac_generator.services.sandbox_code_runner import (
    SANDBOX_BINARY,
    SandboxCodeRunner,
)


def test_sandbox_runner_rejects_empty_code() -> None:
    runner = SandboxCodeRunner()

    with pytest.raises(
        CodeCompilationError,
        match="Code cannot be empty",
    ):
        runner.validate_cpp("")


def test_sandbox_runner_fails_when_runtime_is_missing(
    monkeypatch: MonkeyPatch,
) -> None:
    runner = SandboxCodeRunner()

    monkeypatch.setattr(
        Path,
        "exists",
        lambda _self: False,
    )

    with pytest.raises(
        CodeCompilationError,
        match="Cloud Run sandbox runtime is not available",
    ):
        runner.validate_cpp(
            "#include <iostream>\n"
            "int main() { return 0; }"
        )


def test_sandbox_runner_does_not_fallback_to_local(
    monkeypatch: MonkeyPatch,
) -> None:
    runner = SandboxCodeRunner()

    monkeypatch.setattr(
        Path,
        "exists",
        lambda _self: False,
    )

    called = False

    def fake_local_validate_cpp(
        _self: LocalCodeRunner,
        _code: str,
    ) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(
        LocalCodeRunner,
        "validate_cpp",
        fake_local_validate_cpp,
    )

    with pytest.raises(CodeCompilationError):
        runner.validate_cpp(
            "#include <iostream>\n"
            "int main() { return 0; }"
        )

    assert called is False


def test_sandbox_runner_uses_expected_secure_command(
    monkeypatch: MonkeyPatch,
) -> None:
    runner = SandboxCodeRunner()

    monkeypatch.setattr(
        Path,
        "exists",
        lambda _self: True,
    )

    captured_command: list[str] = []

    def fake_subprocess_run(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        captured_command.extend(command)

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(
        subprocess,
        "run",
        fake_subprocess_run,
    )

    runner.validate_cpp(
        "#include <iostream>\n"
        "int main() { return 0; }"
    )

    assert captured_command[0] == SANDBOX_BINARY
    assert captured_command[1] == "do"

    assert "--write" in captured_command
    assert "--mount" in captured_command
    assert "--workdir" in captured_command

    assert "/workspace" in captured_command
    assert "/bin/bash" in captured_command
    assert "/workspace/run.sh" in captured_command

    assert "--allow-egress" not in captured_command

    mount_index = captured_command.index("--mount")
    mount_value = captured_command[mount_index + 1]

    assert "type=bind" in mount_value
    assert "source=" in mount_value
    assert "destination=/workspace" in mount_value

    workdir_index = captured_command.index("--workdir")

    assert (
        captured_command[workdir_index + 1]
        == "/workspace"
    )


def test_get_code_validator_selects_local_runner(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "code_runner_provider",
        "local",
    )

    validator = get_code_validator()

    assert isinstance(
        validator.runner,
        LocalCodeRunner,
    )


def test_get_code_validator_selects_sandbox_runner(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "code_runner_provider",
        "sandbox",
    )

    validator = get_code_validator()

    assert isinstance(
        validator.runner,
        SandboxCodeRunner,
    )


def test_get_code_validator_rejects_unknown_provider(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "code_runner_provider",
        "unknown",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported code runner provider",
    ):
        get_code_validator()