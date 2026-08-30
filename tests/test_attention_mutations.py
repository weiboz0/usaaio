from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
BOOK2_ROOT = ROOT / "book2"

EXPECTED_MUTATIONS = [
    {
        "id": "b2-019-p06-remove-scaling",
        "notebook": "units/B2-019-attention-transformers/practice/p06_solution.ipynb",
        "mutation_kind": "remove-score-scaling",
        "target_marker": "scores = (q @ k.T) / np.sqrt(q.shape[1])",
        "expected_failure_marker": "np.testing.assert_allclose(weights, EXPECTED_WEIGHTS",
    },
    {
        "id": "b2-019-p08-post-softmax-mask",
        "notebook": "units/B2-019-attention-transformers/practice/p08_solution.ipynb",
        "mutation_kind": "move-mask-after-softmax",
        "target_marker": "masked_scores = scores + mask",
        "expected_failure_marker": "np.testing.assert_allclose(weights, EXPECTED_WEIGHTS",
    },
    {
        "id": "b2-019-p10-wrong-concat-axis",
        "notebook": "units/B2-019-attention-transformers/practice/p10_solution.ipynb",
        "mutation_kind": "concatenate-heads-on-sequence-axis",
        "target_marker": "return heads.transpose(0, 2, 1, 3).reshape(b, n, h * d_h)",
        "expected_failure_marker": "assert recovered.shape == x.shape == (2, 3, 8)",
    },
    {
        "id": "b2-019-p17-omit-position",
        "notebook": "units/B2-019-attention-transformers/practice/p17_solution.ipynb",
        "mutation_kind": "omit-positional-addition",
        "target_marker": "inputs = torch.tensor(X[:-1] + 0.1 * POSITIONAL",
        "expected_failure_marker": "np.testing.assert_allclose(losses[[0, -1]]",
    },
    {
        "id": "b2-019-p24-reverse-residual-layernorm",
        "notebook": "units/B2-019-attention-transformers/practice/p24_solution.ipynb",
        "mutation_kind": "reverse-residual-layernorm-order",
        "target_marker": "y = x + attention_output",
        "expected_failure_marker": "np.testing.assert_allclose(f[1, 2], EXPECTED_NORMALIZED_ROW",
    },
]

EXPECTED_COVERED_POINTS = {
    "attention-mechanism-foundations",
    "self-attention",
    "multi-head-attention",
    "positional-encoding",
    "attention-complexity-analysis",
    "attention-from-scratch",
    "transformer-architecture-foundations",
}


def _mutation_module():
    try:
        return importlib.import_module("tools.verify_attention_mutations")
    except ModuleNotFoundError:
        pytest.fail("tools.verify_attention_mutations must provide the attention mutation runner")


def _write_notebook(path: Path, target_source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "id": "mutation-target",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": target_source,
                    },
                    {
                        "cell_type": "code",
                        "id": "answer-check",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": "assert value == 1  # ANSWER_CHECK\n",
                    },
                ],
                "metadata": {
                    "kernelspec": {
                        "display_name": "Python 3",
                        "language": "python",
                        "name": "python3",
                    }
                },
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
    )


def _spec(module, *, search: str, replacement: str):
    return module.MutationSpec(
        id="fixture-attention-mutation",
        notebook="fixture/solution.ipynb",
        mutation_kind="replace-source",
        target_marker="# MUTATION_TARGET",
        search=search,
        replacement=replacement,
        expected_failure_marker="# ANSWER_CHECK",
    )


def test_attention_registry_has_exactly_five_answer_affecting_mutations() -> None:
    module = _mutation_module()

    actual = [
        {
            "id": mutation.id,
            "notebook": mutation.notebook,
            "mutation_kind": mutation.mutation_kind,
            "target_marker": mutation.target_marker,
            "expected_failure_marker": mutation.expected_failure_marker,
        }
        for mutation in module.MUTATIONS
    ]
    assert actual == EXPECTED_MUTATIONS


def test_each_attention_mutation_binds_one_real_source_and_answer_check() -> None:
    module = _mutation_module()

    for mutation in module.MUTATIONS:
        notebook_path = BOOK2_ROOT / mutation.notebook
        notebook = json.loads(notebook_path.read_text())
        sources = [
            "".join(cell.get("source", ""))
            for cell in notebook["cells"]
            if cell["cell_type"] == "code"
        ]
        assert mutation.target_marker in mutation.search
        assert mutation.search != mutation.replacement
        assert sum(source.count(mutation.target_marker) for source in sources) == 1
        assert sum(source.count(mutation.search) for source in sources) == 1
        assert sum(source.count(mutation.expected_failure_marker) for source in sources) == 1


@pytest.mark.parametrize(
    ("target_source", "search", "match_count"),
    [
        pytest.param("value = 1  # MUTATION_TARGET\n", "missing # MUTATION_TARGET", 0),
        pytest.param(
            "value = 1  # MUTATION_TARGET\nvalue = 1  # MUTATION_TARGET\n",
            "value = 1  # MUTATION_TARGET",
            2,
        ),
    ],
)
def test_attention_runner_fails_closed_on_nonunique_source_match(
    tmp_path: Path, target_source: str, search: str, match_count: int
) -> None:
    module = _mutation_module()
    _write_notebook(tmp_path / "fixture" / "solution.ipynb", target_source)
    spec = _spec(module, search=search, replacement="value = 2  # MUTATION_TARGET")

    with pytest.raises(module.MutationVerificationError, match=rf"matched {match_count}"):
        module.run_mutation(tmp_path, spec)


def test_attention_runner_rejects_a_mutant_that_still_passes(tmp_path: Path) -> None:
    module = _mutation_module()
    _write_notebook(tmp_path / "fixture" / "solution.ipynb", "value = 1  # MUTATION_TARGET\n")
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="value = 1  # mutant still passes # MUTATION_TARGET",
    )

    with pytest.raises(module.MutationVerificationError, match="mutant executed successfully"):
        module.run_mutation(tmp_path, spec)


def test_attention_runner_rejects_failure_before_answer_check(tmp_path: Path) -> None:
    module = _mutation_module()
    _write_notebook(tmp_path / "fixture" / "solution.ipynb", "value = 1  # MUTATION_TARGET\n")
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="raise RuntimeError('early')  # MUTATION_TARGET",
    )

    with pytest.raises(module.MutationVerificationError, match="expected failure at cell 1"):
        module.run_mutation(tmp_path, spec)


def test_attention_runner_rejects_unrelated_exception_in_answer_check_cell(
    tmp_path: Path,
) -> None:
    module = _mutation_module()
    notebook_path = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook_path, "value = 1  # MUTATION_TARGET\n")
    notebook = json.loads(notebook_path.read_text())
    notebook["cells"][1]["source"] = (
        "raise RuntimeError('unrelated failure before assertion')\n"
        "assert value == 1  # ANSWER_CHECK\n"
    )
    notebook_path.write_text(json.dumps(notebook))
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="value = 2  # MUTATION_TARGET",
    )

    with pytest.raises(
        module.MutationVerificationError,
        match="did not fail through the registered answer check",
    ):
        module.run_mutation(tmp_path, spec)


def test_attention_runner_requires_untouched_notebook_to_pass(tmp_path: Path) -> None:
    module = _mutation_module()
    notebook_path = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook_path, "value = 1  # MUTATION_TARGET\n")
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="value = 2  # MUTATION_TARGET",
    )
    module.run_untouched(tmp_path, spec)

    notebook = json.loads(notebook_path.read_text())
    notebook["cells"][0]["source"] = "raise RuntimeError('broken untouched')\n"
    notebook_path.write_text(json.dumps(notebook))
    with pytest.raises(module.MutationVerificationError, match="untouched notebook failed"):
        module.run_untouched(tmp_path, spec)


def test_book2_promotes_exactly_the_seven_attention_points() -> None:
    roadmap = yaml.safe_load((BOOK2_ROOT / "curriculum" / "coverage-map.yaml").read_text())
    points = {row["id"]: row for row in roadmap["knowledge_points"]}

    assert {
        point_id
        for point_id, row in points.items()
        if row["coverage"] == "covered"
        and row.get("destination") == "B2-019-attention-transformers"
    } == EXPECTED_COVERED_POINTS
    for point_id in EXPECTED_COVERED_POINTS:
        row = points[point_id]
        assert row["shipped_concepts"]
        assert row["deficits"]["modalities_missing"] == []
        for evidence in row["evidence_by_modality"].values():
            assert evidence["lesson_anchors"]
            assert evidence["practices"]

    later = {
        point_id
        for point_id, row in points.items()
        if row.get("destination") != "B2-019-attention-transformers"
        and point_id != "nlp-tokenization"
    }
    assert later
    assert {points[point_id]["coverage"] for point_id in later} <= {"missing", "partial"}

    non_target_roadmap = {
        **roadmap,
        "knowledge_points": [
            row
            for row in roadmap["knowledge_points"]
            if row["id"] not in EXPECTED_COVERED_POINTS
        ],
    }
    unchanged_digest = hashlib.sha256(
        json.dumps(
            non_target_roadmap,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    assert unchanged_digest == "8a6a0adddc6f0f284471a759ebd07b6a633a32514d7c049b44b20a696475422b"


def test_attention_manifest_adds_only_the_exact_seven_evidence_claims() -> None:
    manifest = yaml.safe_load(
        (
            BOOK2_ROOT
            / "units"
            / "B2-019-attention-transformers"
            / "manifest.yaml"
        ).read_text()
    )
    claims = manifest.pop("coverage_claims")
    assert [claim["knowledge_point"] for claim in claims] == [
        "attention-mechanism-foundations",
        "self-attention",
        "multi-head-attention",
        "positional-encoding",
        "attention-complexity-analysis",
        "attention-from-scratch",
        "transformer-architecture-foundations",
    ]
    assert all(claim["evidence_concepts"] for claim in claims)
    unchanged_digest = hashlib.sha256(
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    assert unchanged_digest == "f6eb6f6b69a075dab6c590878d5af9fd1e3d94d94b4d7c718231419701aeba39"
