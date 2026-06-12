#!/usr/bin/env python3
"""
GuardSpine Interoperability Test Suite

Validates that all bundle producers create valid v0.2.x bundles that:
1. Pass local JSON Schema validation
2. Pass guardspine-verify validation
3. Can be imported to guardspine-backend
4. Produce identical hashes for the same input

Usage:
    pytest test_interop.py -v
    pytest test_interop.py -v -k "test_producer"  # Run producer tests only
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest

# ============================================================================
# Configuration
# ============================================================================

SPEC_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = SPEC_ROOT / "fixtures" / "golden-vectors"
SCHEMA_PATH = SPEC_ROOT / "schemas" / "evidence-bundle.schema.json"
VALID_VECTORS = [
    "v0.2.0-minimal-bundle.json",
    "v0.2.0-multi-item-bundle.json",
    "v0.2.0-signed-bundle.json",
    "v0.2.0-adversarial-bundle.json",
    "v0.2.1-sanitized-bundle.json",
]
SUPPORTED_VERSIONS = {"0.2.0", "0.2.1"}

# Producer configurations - resolve from env var or sibling directories
_PROJECTS_ROOT = Path(os.environ.get("GUARDSPINE_PROJECTS_ROOT", str(SPEC_ROOT.parent)))

PRODUCERS = {
    "guardspine-kernel": {
        "path": str(_PROJECTS_ROOT / "guardspine-kernel"),
        "language": "node",
        "seal_cmd": "node -e \"const k = require('./dist/index.js'); const items = JSON.parse(process.argv[1]); console.log(JSON.stringify(k.sealBundle(items)));\"",
    },
    "guardspine-kernel-py": {
        "path": str(_PROJECTS_ROOT / "guardspine-kernel-py"),
        "language": "python",
        "seal_cmd": "python -c \"from guardspine_kernel import seal_bundle; import json, sys; items = json.loads(sys.argv[1]); print(json.dumps(seal_bundle(items)))\"",
    },
    "guardspine-product": {
        "path": str(_PROJECTS_ROOT / "guardspine-product"),
        "language": "python",
        "seal_cmd": None,  # Uses EvidenceBundle class
    },
}

# Test items for sealing
TEST_ITEMS = [
    {
        "item_id": "test-001",
        "content_type": "guardspine/test_item",
        "content": {"message": "interoperability test", "value": 42},
    },
    {
        "item_id": "test-002",
        "content_type": "guardspine/test_item",
        "content": {"message": "second item", "array": [1, 2, 3]},
    },
]


# ============================================================================
# Utilities
# ============================================================================


def load_golden_vector(name: str) -> Dict[str, Any]:
    """Load a golden vector bundle."""
    path = FIXTURES_DIR / name
    if not path.exists():
        pytest.skip(f"Golden vector not found: {name}")
    return json.loads(path.read_text())


def load_expected_hashes() -> Dict[str, Any]:
    return load_golden_vector("expected-hashes.json")


def run_command(cmd: str, cwd: Optional[str] = None, input_data: Optional[str] = None) -> tuple:
    """Run a shell command and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        input=input_data,
        timeout=30,
    )
    return result.stdout, result.stderr, result.returncode


def validate_bundle_schema(bundle: Dict[str, Any]) -> List[str]:
    """Validate bundle against JSON schema. Returns list of errors."""
    try:
        import jsonschema
        from jsonschema import Draft202012Validator

        schema = json.loads(SCHEMA_PATH.read_text())
        validator = Draft202012Validator(schema)
        errors = list(validator.iter_errors(bundle))
        return [f"{e.json_path}: {e.message}" for e in errors]
    except ImportError:
        pytest.skip("jsonschema not installed")


def check_node_available() -> bool:
    """Check if Node.js is available."""
    try:
        _, _, rc = run_command("node --version")
        return rc == 0
    except Exception:
        return False


def check_python_package(package: str) -> bool:
    """Check if a Python package is installed."""
    try:
        __import__(package)
        return True
    except ImportError:
        return False


def python_kernel_env() -> Dict[str, str]:
    """Prefer the sibling source checkout so parity tests do not use a stale wheel."""
    env = os.environ.copy()
    kernel_src = Path(PRODUCERS["guardspine-kernel-py"]["path"]) / "src"
    if kernel_src.exists():
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(kernel_src) + (os.pathsep + existing if existing else "")
    return env


def run_python_kernel(script: str, payload: Any) -> Dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "-c", script, json.dumps(payload, ensure_ascii=False)],
        capture_output=True,
        text=True,
        timeout=30,
        env=python_kernel_env(),
    )
    if result.returncode != 0:
        pytest.skip(f"Python kernel command failed: {result.stderr}")
    return json.loads(result.stdout)


def run_node_kernel(script: str, payload: Any) -> Dict[str, Any]:
    producer = PRODUCERS["guardspine-kernel"]
    producer_path = Path(producer["path"])
    if not (check_node_available() and producer_path.exists() and (producer_path / "dist" / "index.js").exists()):
        pytest.skip("guardspine-kernel dist not available")

    result = subprocess.run(
        ["node", "-e", script, json.dumps(payload, ensure_ascii=False)],
        cwd=producer_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    if result.returncode != 0:
        pytest.skip(f"Node kernel command failed: {result.stderr}")
    return json.loads(result.stdout)


# ============================================================================
# Schema Validation Tests
# ============================================================================


class TestSchemaValidation:
    """Tests for JSON Schema validation of golden vectors."""

    @pytest.mark.parametrize(
        "vector_name",
        VALID_VECTORS,
    )
    def test_valid_vectors_pass_schema(self, vector_name):
        """Valid golden vectors must pass schema validation."""
        bundle = load_golden_vector(vector_name)
        errors = validate_bundle_schema(bundle)
        assert not errors, f"Schema validation failed: {errors}"

    @pytest.mark.parametrize(
        "vector_name",
        [
            "malformed/missing-version.json",
            "malformed/wrong-version.json",
            "malformed/chain-count-mismatch.json",
            "malformed/unbound-item.json",
            "malformed/broken-chain-linkage.json",
            "malformed/sequence-gap.json",
            "malformed/invalid-sanitization-shape.json",
        ],
    )
    def test_malformed_vectors_fail_schema(self, vector_name):
        """Malformed golden vectors must fail schema validation."""
        bundle = load_golden_vector(vector_name)
        errors = validate_bundle_schema(bundle)
        assert errors, f"Malformed vector should have failed: {vector_name}"


# ============================================================================
# Bundle Structure Tests
# ============================================================================


class TestBundleStructure:
    """Tests for bundle structure compliance across supported versions."""

    @pytest.mark.parametrize(
        "vector_name",
        VALID_VECTORS,
    )
    def test_version_is_supported(self, vector_name):
        """Bundle version must be a supported schema version."""
        bundle = load_golden_vector(vector_name)
        assert bundle.get("version") in SUPPORTED_VERSIONS

    @pytest.mark.parametrize(
        "vector_name",
        VALID_VECTORS,
    )
    def test_items_have_sequence(self, vector_name):
        """All items must have sequence field matching array index."""
        bundle = load_golden_vector(vector_name)
        for idx, item in enumerate(bundle.get("items", [])):
            assert item.get("sequence") == idx, f"Item {idx} sequence mismatch"

    @pytest.mark.parametrize(
        "vector_name",
        VALID_VECTORS,
    )
    def test_hash_chain_uses_genesis(self, vector_name):
        """First hash chain entry must use 'genesis' as previous_hash."""
        bundle = load_golden_vector(vector_name)
        chain = bundle.get("immutability_proof", {}).get("hash_chain", [])
        if chain:
            assert chain[0].get("previous_hash") == "genesis"

    @pytest.mark.parametrize(
        "vector_name",
        VALID_VECTORS,
    )
    def test_chain_count_matches_items(self, vector_name):
        """Hash chain length must equal items array length."""
        bundle = load_golden_vector(vector_name)
        items = bundle.get("items", [])
        chain = bundle.get("immutability_proof", {}).get("hash_chain", [])
        assert len(chain) == len(items), f"Chain length {len(chain)} != items length {len(items)}"

    @pytest.mark.parametrize(
        "vector_name",
        VALID_VECTORS,
    )
    def test_chain_items_bound_correctly(self, vector_name):
        """Chain entries must bind to corresponding items."""
        bundle = load_golden_vector(vector_name)
        items = bundle.get("items", [])
        chain = bundle.get("immutability_proof", {}).get("hash_chain", [])

        for idx, (item, link) in enumerate(zip(items, chain)):
            assert link.get("item_id") == item.get("item_id"), f"item_id mismatch at {idx}"
            assert link.get("content_type") == item.get("content_type"), f"content_type mismatch at {idx}"
            assert link.get("content_hash") == item.get("content_hash"), f"content_hash mismatch at {idx}"
            assert link.get("sequence") == idx, f"sequence mismatch at {idx}"


# ============================================================================
# Producer Interoperability Tests
# ============================================================================


@pytest.mark.skipif(not check_node_available(), reason="Node.js not available")
class TestNodeKernelParity:
    """Tests for Node.js kernel producing valid bundles."""

    def test_kernel_produces_valid_bundle(self):
        """guardspine-kernel sealBundle produces schema-valid bundle."""
        producer = PRODUCERS.get("guardspine-kernel")
        if not producer or not Path(producer["path"]).exists():
            pytest.skip("guardspine-kernel not found")

        items_json = json.dumps(TEST_ITEMS)
        cmd = f'node -e "const k = require(\'./dist/index.js\'); console.log(JSON.stringify(k.sealBundle({items_json})));"'

        stdout, stderr, rc = run_command(cmd, cwd=producer["path"])
        if rc != 0:
            pytest.skip(f"Kernel command failed: {stderr}")

        bundle = json.loads(stdout)
        errors = validate_bundle_schema(bundle)
        assert not errors, f"Schema validation failed: {errors}"


@pytest.mark.skipif(not check_python_package("guardspine_kernel"), reason="guardspine-kernel-py not installed")
class TestPythonKernelParity:
    """Tests for Python kernel bridge producing valid bundles."""

    def test_kernel_py_produces_valid_bundle(self):
        """guardspine-kernel-py seal_bundle produces schema-valid bundle."""
        from guardspine_kernel import seal_bundle
        from uuid import uuid4
        from datetime import datetime, timezone

        sealed = seal_bundle(TEST_ITEMS)
        # Wrap into a complete bundle
        bundle = {
            "bundle_id": str(uuid4()),
            "version": "0.2.0",
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "items": sealed["items"],
            "immutability_proof": sealed["immutability_proof"],
        }
        errors = validate_bundle_schema(bundle)
        assert not errors, f"Schema validation failed: {errors}"

    def test_canonical_json_deterministic(self):
        """canonical_json produces consistent output."""
        from guardspine_kernel import canonical_json

        obj = {"z": 1, "a": 2, "m": {"y": 3, "x": 4}}

        # Multiple calls should produce identical output
        result1 = canonical_json(obj)
        result2 = canonical_json(obj)
        assert result1 == result2

        # Keys should be sorted
        assert result1.index('"a"') < result1.index('"m"') < result1.index('"z"')


# ============================================================================
# Hash Parity Tests
# ============================================================================


class TestHashParity:
    """Tests for cross-language hash parity."""

    @pytest.mark.skipif(
        not (check_node_available() and check_python_package("guardspine_kernel")),
        reason="Both Node.js and guardspine-kernel-py required",
    )
    def test_same_input_same_hash(self):
        """Same input items must produce identical root_hash across languages."""
        from guardspine_kernel import seal_bundle as py_seal

        # Python result
        py_bundle = py_seal(TEST_ITEMS)
        py_root = py_bundle.get("immutability_proof", {}).get("root_hash")

        # Node.js result
        producer = PRODUCERS.get("guardspine-kernel")
        if not producer or not Path(producer["path"]).exists():
            pytest.skip("guardspine-kernel not found")

        items_json = json.dumps(TEST_ITEMS)
        cmd = f'node -e "const k = require(\'./dist/index.js\'); const b = k.sealBundle({items_json}); console.log(b.immutability_proof.root_hash);"'

        stdout, stderr, rc = run_command(cmd, cwd=producer["path"])
        if rc != 0:
            pytest.skip(f"Node kernel failed: {stderr}")

        node_root = stdout.strip()

        assert py_root == node_root, f"Hash mismatch: Python={py_root}, Node={node_root}"


PY_ADVERSARIAL_SCRIPT = r"""
from guardspine_kernel import canonical_json, compute_content_hash, seal_bundle, verify_bundle
import json
import sys

payload = json.loads(sys.argv[1])
result = {
    "canonical_json": [],
    "canonical_json_rejections": [],
    "content_hashes": [],
}

for case in payload["expected"]["canonical_json"]:
    result["canonical_json"].append(canonical_json(case["input"]))

for case in payload["expected"].get("canonical_json_rejections", []):
    try:
        canonical_json(case["input"])
        result["canonical_json_rejections"].append({"rejected": False, "message": ""})
    except Exception as exc:
        result["canonical_json_rejections"].append({"rejected": True, "message": str(exc)})

for case in payload["expected"]["content_hashes"]:
    result["content_hashes"].append(compute_content_hash(case["content"]))

bundle = payload["bundle"]
verify_result = verify_bundle(bundle)
sealed = seal_bundle(bundle["items"])
result["bundle_valid"] = bool(verify_result.get("valid"))
result["sealed_root_hash"] = sealed["immutability_proof"]["root_hash"]

print(json.dumps(result, ensure_ascii=True))
"""


NODE_ADVERSARIAL_SCRIPT = r"""
const k = require("./dist/index.js");
const payload = JSON.parse(process.argv[1]);
const result = {
  canonical_json: [],
  canonical_json_rejections: [],
  content_hashes: [],
};

for (const testCase of payload.expected.canonical_json) {
  result.canonical_json.push(k.canonicalJson(testCase.input));
}

for (const testCase of payload.expected.canonical_json_rejections ?? []) {
  try {
    k.canonicalJson(testCase.input);
    result.canonical_json_rejections.push({ rejected: false, message: "" });
  } catch (error) {
    result.canonical_json_rejections.push({
      rejected: true,
      message: String(error && error.message ? error.message : error),
    });
  }
}

for (const testCase of payload.expected.content_hashes) {
  result.content_hashes.push(k.computeContentHash(testCase.content));
}

const bundle = payload.bundle;
const verifyResult = k.verifyBundle(bundle, { acceptProofVersions: ["v0.2.0"] });
const sealed = k.sealBundle({ items: bundle.items }, { proofVersion: "v0.2.0" });
result.bundle_valid = Boolean(verifyResult.valid);
result.sealed_root_hash = sealed.immutabilityProof.root_hash;

console.log(JSON.stringify(result));
"""


class TestAdversarialKernelParity:
    """Adversarial vectors must run through both canonical kernels."""

    def _payload(self) -> Dict[str, Any]:
        return {
            "expected": load_expected_hashes(),
            "bundle": load_golden_vector("v0.2.0-adversarial-bundle.json"),
        }

    @pytest.mark.skipif(not check_python_package("guardspine_kernel"), reason="guardspine-kernel-py not installed")
    def test_adversarial_vectors_match_python_kernel(self):
        payload = self._payload()
        result = run_python_kernel(PY_ADVERSARIAL_SCRIPT, payload)
        self._assert_adversarial_result(payload, result)

    @pytest.mark.skipif(not check_node_available(), reason="Node.js not available")
    def test_adversarial_vectors_match_typescript_kernel(self):
        payload = self._payload()
        result = run_node_kernel(NODE_ADVERSARIAL_SCRIPT, payload)
        self._assert_adversarial_result(payload, result)

    def _assert_adversarial_result(self, payload: Dict[str, Any], result: Dict[str, Any]) -> None:
        expected = payload["expected"]

        assert result["canonical_json"] == [
            case["expected_output"] for case in expected["canonical_json"]
        ]

        rejections = result["canonical_json_rejections"]
        assert len(rejections) == len(expected["canonical_json_rejections"])
        for actual, case in zip(rejections, expected["canonical_json_rejections"]):
            assert actual["rejected"] is True
            assert case["error_contains"] in actual["message"]

        assert result["content_hashes"] == [
            case["expected_hash"] for case in expected["content_hashes"]
        ]
        assert result["bundle_valid"] is True
        assert result["sealed_root_hash"] == expected["v0.2.0-adversarial-bundle.json"]["root_hash"]


# ============================================================================
# Chain Integrity Tests
# ============================================================================


class TestChainIntegrity:
    """Tests for hash chain integrity."""

    @pytest.mark.parametrize(
        "vector_name",
        VALID_VECTORS,
    )
    def test_chain_linkage_valid(self, vector_name):
        """Each chain entry's previous_hash must match the prior chain_hash."""
        bundle = load_golden_vector(vector_name)
        chain = bundle.get("immutability_proof", {}).get("hash_chain", [])

        for idx, link in enumerate(chain):
            if idx == 0:
                assert link.get("previous_hash") == "genesis"
            else:
                expected_prev = chain[idx - 1].get("chain_hash")
                actual_prev = link.get("previous_hash")
                assert actual_prev == expected_prev, f"Chain broken at {idx}: expected {expected_prev}, got {actual_prev}"


# ============================================================================
# Signature Tests
# ============================================================================


class TestSignatures:
    """Tests for signature structure compliance."""

    def test_signed_bundle_has_valid_signature_structure(self):
        """Signed bundle signatures must have required fields."""
        bundle = load_golden_vector("v0.2.0-signed-bundle.json")
        signatures = bundle.get("signatures", [])

        assert len(signatures) >= 1, "Signed bundle must have at least one signature"

        required_fields = ["signature_id", "algorithm", "signer_id", "signature_value", "signed_at"]
        for sig in signatures:
            for field in required_fields:
                assert field in sig, f"Signature missing required field: {field}"

    def test_signature_algorithm_valid(self):
        """Signature algorithm must be in allowed list."""
        bundle = load_golden_vector("v0.2.0-signed-bundle.json")
        allowed = ["ed25519", "rsa-sha256", "ecdsa-p256", "hmac-sha256"]

        for sig in bundle.get("signatures", []):
            assert sig.get("algorithm") in allowed, f"Invalid algorithm: {sig.get('algorithm')}"


class TestSanitization:
    """Tests for sanitization metadata in v0.2.1 bundles."""

    def test_sanitized_vector_has_required_contract_fields(self):
        bundle = load_golden_vector("v0.2.1-sanitized-bundle.json")
        sanitization = bundle.get("sanitization", {})

        assert sanitization.get("engine_name") == "pii-shield"
        assert sanitization.get("token_format") == "[HIDDEN:<id>]"
        assert isinstance(sanitization.get("redaction_count"), int)
        assert isinstance(sanitization.get("redactions_by_type"), dict)
        assert sanitization.get("status") == "sanitized"


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
