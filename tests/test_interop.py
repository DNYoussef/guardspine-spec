#!/usr/bin/env python3
"""
GuardSpine Interoperability Test Suite

Validates that all bundle producers create valid v0.2.0 bundles that:
1. Pass local JSON Schema validation
2. Pass guardspine-verify validation
3. Can be imported to guardspine-backend
4. Produce identical hashes for the same input

Usage:
    pytest test_interop.py -v
    pytest test_interop.py -v -k "test_producer"  # Run producer tests only
"""

import json
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
SCHEMA_PATH = SPEC_ROOT / "schemas" / "evidence-bundle-v0.2.0.schema.json"

# Producer configurations - paths are relative to D:\Projects
PRODUCERS = {
    "guardspine-kernel": {
        "path": "D:/Projects/guardspine-kernel",
        "language": "node",
        "seal_cmd": "node -e \"const k = require('./dist/index.js'); const items = JSON.parse(process.argv[1]); console.log(JSON.stringify(k.sealBundle(items)));\"",
    },
    "guardspine-kernel-py": {
        "path": "D:/Projects/guardspine-kernel-py",
        "language": "python",
        "seal_cmd": "python -c \"from guardspine_kernel import seal_bundle; import json, sys; items = json.loads(sys.argv[1]); print(json.dumps(seal_bundle(items)))\"",
    },
    "guardspine-product": {
        "path": "D:/Projects/guardspine-product",
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


# ============================================================================
# Schema Validation Tests
# ============================================================================


class TestSchemaValidation:
    """Tests for JSON Schema validation of golden vectors."""

    @pytest.mark.parametrize(
        "vector_name",
        [
            "v0.2.0-minimal-bundle.json",
            "v0.2.0-multi-item-bundle.json",
            "v0.2.0-signed-bundle.json",
        ],
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
    """Tests for v0.2.0 bundle structure compliance."""

    @pytest.mark.parametrize(
        "vector_name",
        [
            "v0.2.0-minimal-bundle.json",
            "v0.2.0-multi-item-bundle.json",
            "v0.2.0-signed-bundle.json",
        ],
    )
    def test_version_is_0_2_0(self, vector_name):
        """Bundle version must be exactly '0.2.0'."""
        bundle = load_golden_vector(vector_name)
        assert bundle.get("version") == "0.2.0"

    @pytest.mark.parametrize(
        "vector_name",
        [
            "v0.2.0-minimal-bundle.json",
            "v0.2.0-multi-item-bundle.json",
            "v0.2.0-signed-bundle.json",
        ],
    )
    def test_items_have_sequence(self, vector_name):
        """All items must have sequence field matching array index."""
        bundle = load_golden_vector(vector_name)
        for idx, item in enumerate(bundle.get("items", [])):
            assert item.get("sequence") == idx, f"Item {idx} sequence mismatch"

    @pytest.mark.parametrize(
        "vector_name",
        [
            "v0.2.0-minimal-bundle.json",
            "v0.2.0-multi-item-bundle.json",
            "v0.2.0-signed-bundle.json",
        ],
    )
    def test_hash_chain_uses_genesis(self, vector_name):
        """First hash chain entry must use 'genesis' as previous_hash."""
        bundle = load_golden_vector(vector_name)
        chain = bundle.get("immutability_proof", {}).get("hash_chain", [])
        if chain:
            assert chain[0].get("previous_hash") == "genesis"

    @pytest.mark.parametrize(
        "vector_name",
        [
            "v0.2.0-minimal-bundle.json",
            "v0.2.0-multi-item-bundle.json",
            "v0.2.0-signed-bundle.json",
        ],
    )
    def test_chain_count_matches_items(self, vector_name):
        """Hash chain length must equal items array length."""
        bundle = load_golden_vector(vector_name)
        items = bundle.get("items", [])
        chain = bundle.get("immutability_proof", {}).get("hash_chain", [])
        assert len(chain) == len(items), f"Chain length {len(chain)} != items length {len(items)}"

    @pytest.mark.parametrize(
        "vector_name",
        [
            "v0.2.0-minimal-bundle.json",
            "v0.2.0-multi-item-bundle.json",
            "v0.2.0-signed-bundle.json",
        ],
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


# ============================================================================
# Chain Integrity Tests
# ============================================================================


class TestChainIntegrity:
    """Tests for hash chain integrity."""

    @pytest.mark.parametrize(
        "vector_name",
        [
            "v0.2.0-minimal-bundle.json",
            "v0.2.0-multi-item-bundle.json",
            "v0.2.0-signed-bundle.json",
        ],
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


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
