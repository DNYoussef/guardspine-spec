#!/usr/bin/env python3
"""
GuardSpine End-to-End Pipeline Test Suite

Validates the full evidence pipeline:
1. Create evidence items from agent actions
2. Seal items into a bundle using guardspine-kernel
3. Verify bundle locally
4. Import bundle to backend (if available)
5. Export bundle and re-verify

Usage:
    pytest test_e2e.py -v
    pytest test_e2e.py -v -k "test_full_pipeline"
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
import pytest

# ============================================================================
# Configuration
# ============================================================================

SPEC_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = SPEC_ROOT / "fixtures" / "golden-vectors"
SCHEMA_PATH = SPEC_ROOT / "schemas" / "evidence-bundle-v0.2.0.schema.json"

# Backend API (optional - tests skip gracefully if not available)
BACKEND_URL = os.getenv("GUARDSPINE_BACKEND_URL", "http://localhost:8000")
BACKEND_API_KEY = os.getenv("GUARDSPINE_API_KEY", "")


# ============================================================================
# Utilities
# ============================================================================


def generate_uuid() -> str:
    """Generate a UUID v4 string."""
    return str(uuid4())


def iso_timestamp() -> str:
    """Get current ISO 8601 timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def check_python_package(package: str) -> bool:
    """Check if a Python package is installed."""
    try:
        __import__(package)
        return True
    except ImportError:
        return False


def check_backend_available() -> bool:
    """Check if guardspine-backend is reachable."""
    try:
        import httpx

        response = httpx.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


# ============================================================================
# Evidence Item Factories
# ============================================================================


def create_diff_item(
    from_version: str,
    to_version: str,
    changes: List[Dict[str, Any]],
    artifact_id: str = "test-artifact",
) -> Dict[str, Any]:
    """Create a diff evidence item."""
    return {
        "item_id": generate_uuid(),
        "content_type": "guardspine/diff",
        "content": {
            "diff_id": f"diff-{from_version}-{to_version}",
            "artifact_id": artifact_id,
            "from_version": from_version,
            "to_version": to_version,
            "algorithm": "unified",
            "changes": changes,
            "stats": {
                "additions": sum(1 for c in changes if c.get("type") == "add"),
                "deletions": sum(1 for c in changes if c.get("type") == "remove"),
            },
        },
    }


def create_policy_evaluation_item(
    policy_id: str,
    result: str,
    findings: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Create a policy evaluation evidence item."""
    return {
        "item_id": generate_uuid(),
        "content_type": "guardspine/policy_evaluation",
        "content": {
            "evaluation_id": generate_uuid(),
            "policy_id": policy_id,
            "policy_version": "1.0.0",
            "result": result,
            "findings": findings or [],
            "evaluated_at": iso_timestamp(),
        },
    }


def create_approval_item(
    approver_id: str,
    decision: str,
    rationale: str,
    conditions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create an approval evidence item."""
    return {
        "item_id": generate_uuid(),
        "content_type": "guardspine/approval",
        "content": {
            "approval_id": generate_uuid(),
            "approver": {
                "signer_id": approver_id,
                "signer_type": "human",
            },
            "decision": decision,
            "rationale": rationale,
            "conditions": conditions or [],
            "decided_at": iso_timestamp(),
        },
    }


# ============================================================================
# Pipeline Steps
# ============================================================================


def seal_bundle_python(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Seal items into a bundle using guardspine-kernel-py."""
    from guardspine_kernel import seal_bundle

    sealed = seal_bundle(items)
    # Wrap into a complete bundle
    return {
        "bundle_id": generate_uuid(),
        "version": "0.2.0",
        "created_at": iso_timestamp(),
        "items": sealed["items"],
        "immutability_proof": sealed["immutability_proof"],
    }


def verify_bundle_python(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Verify a bundle using guardspine-kernel-py."""
    from guardspine_kernel import verify_bundle

    return verify_bundle(bundle)


def validate_bundle_schema(bundle: Dict[str, Any]) -> List[str]:
    """Validate bundle against JSON schema."""
    try:
        import jsonschema
        from jsonschema import Draft202012Validator

        schema = json.loads(SCHEMA_PATH.read_text())
        validator = Draft202012Validator(schema)
        return [f"{e.json_path}: {e.message}" for e in validator.iter_errors(bundle)]
    except ImportError:
        return []


async def import_bundle_to_backend(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Import bundle to guardspine-backend."""
    import httpx

    headers = {"Authorization": f"Bearer {BACKEND_API_KEY}"} if BACKEND_API_KEY else {}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/api/v1/bundles/import",
            json=bundle,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


async def export_bundle_from_backend(bundle_id: str) -> Dict[str, Any]:
    """Export bundle from guardspine-backend."""
    import httpx

    headers = {"Authorization": f"Bearer {BACKEND_API_KEY}"} if BACKEND_API_KEY else {}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_URL}/api/v1/bundles/import/{bundle_id}/export/spec",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


# ============================================================================
# E2E Pipeline Tests
# ============================================================================


@pytest.mark.skipif(
    not check_python_package("guardspine_kernel"),
    reason="guardspine-kernel-py not installed",
)
class TestE2EPipeline:
    """End-to-end pipeline tests."""

    def test_create_seal_verify_local(self):
        """Full local pipeline: create -> seal -> verify."""
        # 1. Create evidence items
        items = [
            create_diff_item(
                from_version="v1.0.0",
                to_version="v1.1.0",
                changes=[
                    {"type": "add", "content": "new feature added"},
                    {"type": "remove", "content": "deprecated code removed"},
                ],
            ),
            create_policy_evaluation_item(
                policy_id="code-review-policy",
                result="pass",
                findings=[
                    {
                        "finding_id": "f-001",
                        "severity": "info",
                        "message": "Code meets standards",
                    }
                ],
            ),
            create_approval_item(
                approver_id="usr-test-approver",
                decision="approved",
                rationale="Change is safe and tested",
            ),
        ]

        # 2. Seal items into bundle
        bundle = seal_bundle_python(items)

        # 3. Validate schema
        schema_errors = validate_bundle_schema(bundle)
        assert not schema_errors, f"Schema validation failed: {schema_errors}"

        # 4. Verify bundle
        result = verify_bundle_python(bundle)
        assert result.get("valid") is True, f"Verification failed: {result}"

        # 5. Check structure
        assert bundle.get("version") == "0.2.0"
        assert len(bundle.get("items", [])) == 3
        assert len(bundle.get("immutability_proof", {}).get("hash_chain", [])) == 3

    def test_bundle_items_have_correct_sequence(self):
        """Items in sealed bundle have correct sequence numbers."""
        items = [
            create_diff_item("v1", "v2", []),
            create_policy_evaluation_item("policy-1", "pass"),
            create_approval_item("user-1", "approved", "ok"),
        ]

        bundle = seal_bundle_python(items)

        for idx, item in enumerate(bundle.get("items", [])):
            assert item.get("sequence") == idx, f"Item {idx} has wrong sequence"

    def test_bundle_chain_linkage_correct(self):
        """Hash chain entries link correctly."""
        items = [
            create_diff_item("v1", "v2", []),
            create_policy_evaluation_item("policy-1", "pass"),
        ]

        bundle = seal_bundle_python(items)
        chain = bundle.get("immutability_proof", {}).get("hash_chain", [])

        # First entry uses genesis
        assert chain[0].get("previous_hash") == "genesis"

        # Second entry links to first
        assert chain[1].get("previous_hash") == chain[0].get("chain_hash")

    def test_bundle_root_hash_deterministic(self):
        """Same items produce same root_hash."""
        # Fixed items for determinism
        items = [
            {
                "item_id": "fixed-id-001",
                "content_type": "guardspine/test",
                "content": {"value": 42},
            }
        ]

        bundle1 = seal_bundle_python(items)
        bundle2 = seal_bundle_python(items)

        root1 = bundle1.get("immutability_proof", {}).get("root_hash")
        root2 = bundle2.get("immutability_proof", {}).get("root_hash")

        assert root1 == root2, f"Root hash mismatch: {root1} != {root2}"

    def test_tampered_bundle_fails_verification(self):
        """Bundle with tampered content fails verification."""
        items = [create_diff_item("v1", "v2", [{"type": "add", "content": "original"}])]

        bundle = seal_bundle_python(items)

        # Tamper with content
        bundle["items"][0]["content"]["changes"][0]["content"] = "tampered"

        result = verify_bundle_python(bundle)
        assert result.get("valid") is False, "Tampered bundle should fail verification"


@pytest.mark.skipif(
    not check_python_package("guardspine_kernel"),
    reason="guardspine-kernel-py not installed",
)
@pytest.mark.skipif(not check_backend_available(), reason="Backend not available")
@pytest.mark.asyncio
class TestE2EPipelineWithBackend:
    """E2E tests that include backend integration."""

    async def test_full_pipeline_with_backend(self):
        """Complete pipeline: create -> seal -> verify -> import -> export -> verify."""
        # 1. Create evidence items
        items = [
            create_diff_item(
                from_version="v1.0.0",
                to_version="v1.1.0",
                changes=[{"type": "add", "content": "test change"}],
            ),
            create_approval_item(
                approver_id="usr-e2e-test",
                decision="approved",
                rationale="E2E test approval",
            ),
        ]

        # 2. Seal bundle
        bundle = seal_bundle_python(items)
        original_root_hash = bundle.get("immutability_proof", {}).get("root_hash")

        # 3. Verify locally
        local_result = verify_bundle_python(bundle)
        assert local_result.get("valid") is True

        # 4. Import to backend
        import_result = await import_bundle_to_backend(bundle)
        assert import_result.get("success") is True
        bundle_id = import_result.get("bundle_id")
        assert bundle_id is not None

        # 5. Export from backend
        exported_bundle = await export_bundle_from_backend(bundle_id)

        # 6. Verify exported bundle
        export_result = verify_bundle_python(exported_bundle)
        assert export_result.get("valid") is True

        # 7. Root hash should match
        exported_root_hash = exported_bundle.get("immutability_proof", {}).get("root_hash")
        assert original_root_hash == exported_root_hash, "Root hash changed after import/export"


# ============================================================================
# Security Tests
# ============================================================================


@pytest.mark.skipif(not check_backend_available(), reason="Backend not available")
@pytest.mark.asyncio
class TestSecurityE2E:
    """Security-focused E2E tests."""

    async def test_l4_approval_requires_auth(self):
        """L4 approval endpoint requires authentication."""
        import httpx

        async with httpx.AsyncClient() as client:
            # Try to create approval without auth
            response = await client.post(
                f"{BACKEND_URL}/api/v1/approvals/create",
                json={"action_id": "test", "decision": "approve"},
                timeout=10,
            )
            assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    async def test_unknown_tool_defaults_to_l3(self):
        """Unknown tools should default to L3 review."""
        import httpx

        headers = {"Authorization": f"Bearer {BACKEND_API_KEY}"} if BACKEND_API_KEY else {}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/evaluate",
                json={
                    "tool_name": "completely_unknown_tool_xyz",
                    "action": "execute",
                },
                headers=headers,
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                # Should require at least L3 review
                assert data.get("risk_tier", "L0") >= "L3" or data.get("requires_review") is True


# ============================================================================
# Regression Tests
# ============================================================================


class TestRegression:
    """Regression tests to ensure valid bundles stay valid."""

    @pytest.mark.parametrize(
        "vector_name",
        [
            "v0.2.0-minimal-bundle.json",
            "v0.2.0-multi-item-bundle.json",
            "v0.2.0-signed-bundle.json",
        ],
    )
    def test_golden_vectors_remain_valid(self, vector_name):
        """Golden vectors must remain schema-valid."""
        path = FIXTURES_DIR / vector_name
        if not path.exists():
            pytest.skip(f"Golden vector not found: {vector_name}")

        bundle = json.loads(path.read_text())
        errors = validate_bundle_schema(bundle)
        assert not errors, f"Regression: {vector_name} now fails validation: {errors}"


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
