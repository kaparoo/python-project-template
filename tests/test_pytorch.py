from __future__ import annotations

from typing import TYPE_CHECKING

from tests.helpers import prose

if TYPE_CHECKING:
    from tests.helpers import Render


def test_torch_in_dependencies(render: Render) -> None:
    project = render()
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '"torch>=2.12.1"' in pyproject
    assert '"torchvision>=0.27.1"' in pyproject
    assert "Artificial Intelligence" in pyproject


def test_cuda_backend_routes_to_cuda_index(render: Render) -> None:
    project = render()
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "[[tool.uv.index]]" in pyproject
    assert "https://download.pytorch.org/whl/cu130" in pyproject
    assert "[tool.uv.sources]" in pyproject
    assert 'torch = { index = "pytorch" }' in pyproject
    assert 'torchvision = { index = "pytorch" }' in pyproject


def test_cpu_backend_routes_to_cpu_index(render: Render) -> None:
    project = render({"compute_backend": "cpu"})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "https://download.pytorch.org/whl/cpu" in pyproject
    assert "cu130" not in pyproject


def test_readme_documents_compute_environment(render: Render) -> None:
    project = render()
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "## 🖥️ Compute environment" in readme
    assert "badge/PyTorch-2.12.1" in readme
    assert "badge/CUDA-13.0" in readme
    assert "https://download.pytorch.org/whl/cu130" in readme
    assert (
        "[`pyproject.toml`](https://github.com/kaparoo/test-app/blob/main/pyproject.toml)"
        in readme
    )

    cpu_app = render({"compute_backend": "cpu", "is_library": False})
    readme = (cpu_app / "README.md").read_text(encoding="utf-8")
    assert "badge/CUDA" not in readme
    assert "https://download.pytorch.org/whl/cpu" in readme
    assert "[`pyproject.toml`](./pyproject.toml)" in readme


def test_agents_md_names_the_pytorch_variant(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "- `torch` / `torchvision`: deep learning runtime" in agents
    assert "`copier update --UNSAFE --vcs-ref pytorch`" in agents
    answers = (project / ".copier-answers.yml").read_text(encoding="utf-8")
    assert "copier update --vcs-ref pytorch" in answers


def test_dependency_guide_covers_torch(render: Render) -> None:
    project = render()
    deps = (project / ".agents" / "dependencies.md").read_text(encoding="utf-8")
    assert "uv sync --locked" not in deps
    assert "CI's `lock` job runs `uv lock --check`" in prose(deps)
    assert "`torch` and `torchvision` install from the `pytorch` index" in prose(deps)
    assert "moves the README's PyTorch badge" in prose(deps)
    assert "The newest version is also capped by `torch`" in prose(deps)


def test_pytest_projects_get_a_cuda_skip_mark(render: Render) -> None:
    project = render({"use_pytest": True})
    marks = (project / "tests" / "marks.py").read_text(encoding="utf-8")
    assert "requires_cuda = pytest.mark.skipif(" in marks
    assert "not torch.cuda.is_available()" in marks
    assert 'reason="needs a CUDA device"' in marks
    tests = (project / "tests" / "AGENTS.md").read_text(encoding="utf-8")
    assert "`tests/marks.py` starts with `requires_cuda`" in prose(tests)

    project = render()
    assert not (project / "tests").exists()
