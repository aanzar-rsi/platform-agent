"""Provision an end-to-end procurement preflight scenario across both systems.

This script prepares:
1) platform-agent Postgres: tenant, roles, permissions, users, memberships,
   MCP server connection, and tenant policy mappings for procurement BAPIs.
2) toyerp-mcp HTTP admin: roles/users/tool grants and per-user bearer tokens.

Run from repository root:
    python3 scripts/setup_preflight_toyerp_procurement.py

Required env vars:
    TOYERP_ADMIN_USERNAME
    TOYERP_ADMIN_PASSWORD

Optional env vars:
    TOYERP_BASE_URL (default http://127.0.0.1:8000)
    PLATFORM_TENANT_ID (default 65f0a1b2c3d4e5f607182901)
"""

from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import psycopg
from psycopg.types.json import Jsonb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from api.core.security import hash_password
from src.config import settings

TOYERP_BAPIS = {
    "vendor.read": "BAPI_VENDOR_GETLIST",
    "vendor.detail": "BAPI_VENDOR_GETDETAIL",
    "material.read": "BAPI_MATERIAL_GETLIST",
    "purchase_order.read": "BAPI_PO_GETLIST",
    "purchase_order.detail": "BAPI_PO_GETDETAIL",
    "purchase_order.create": "BAPI_PO_CREATE",
    "purchase_order.change": "BAPI_PO_CHANGE",
    "goods_receipt.create": "BAPI_GOODSMVT_CREATE",
    "ap_invoice.create": "BAPI_INCOMINGINVOICE_CREATE",
    "ap_payment.post": "BAPI_AP_PAYMENT_POST",
}


@dataclass(frozen=True)
class PlatformUser:
    username: str
    email: str
    display_name: str
    password: str
    role_name: str
    toyerp_username: str


USERS = [
    PlatformUser(
        username="buyer1",
        email="buyer1@toyerp.local",
        display_name="Buyer One",
        password="Buyer@123456",
        role_name="Procurement Buyer",
        toyerp_username="buyer",
    ),
    PlatformUser(
        username="apclerk1",
        email="apclerk1@toyerp.local",
        display_name="AP Clerk One",
        password="Apclerk@123456",
        role_name="AP Clerk",
        toyerp_username="apclerk",
    ),
    PlatformUser(
        username="auditor1",
        email="auditor1@toyerp.local",
        display_name="Auditor One",
        password="Auditor@123456",
        role_name="Read Only Auditor",
        toyerp_username="auditor",
    ),
]


ROLE_PERMISSIONS = {
    "Procurement Buyer": [
        "vendor.read",
        "vendor.detail",
        "material.read",
        "purchase_order.read",
        "purchase_order.detail",
        "purchase_order.create",
        "purchase_order.change",
        "goods_receipt.create",
    ],
    "AP Clerk": [
        "vendor.read",
        "purchase_order.read",
        "purchase_order.detail",
        "ap_invoice.create",
        "ap_payment.post",
    ],
    "Read Only Auditor": [
        "vendor.read",
        "vendor.detail",
        "material.read",
        "purchase_order.read",
        "purchase_order.detail",
    ],
}


def _stable_id(kind: str, *values: str) -> str:
    raw = ":".join((kind, *values))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _toyerp_login(base_url: str, username: str, password: str) -> str:
    response = requests.post(
        f"{base_url.rstrip('/')}/auth/login",
        json={"username": username, "password": password},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError(f"ToyERP login did not return access_token for {username}")
    return token


def _toyerp_admin(base_url: str, token: str, operation: str, payload: dict[str, Any]) -> None:
    response = requests.post(
        f"{base_url.rstrip('/')}/admin/{operation}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"ToyERP admin {operation} failed: {response.status_code} {response.text}")


def setup_toyerp_users(base_url: str, admin_user: str, admin_password: str) -> dict[str, str]:
    admin_token = _toyerp_login(base_url, admin_user, admin_password)

    toyerp_users = {
        "buyer": ("Buyer@123456", "purchasing"),
        "apclerk": ("Apclerk@123456", "ap_clerk"),
        "auditor": ("Auditor@123456", "auditor"),
    }
    role_tools = {
        "purchasing": [
            "BAPI_VENDOR_GETLIST", "BAPI_VENDOR_GETDETAIL", "BAPI_MATERIAL_GETLIST",
            "BAPI_PO_GETLIST", "BAPI_PO_GETDETAIL", "BAPI_PO_CREATE",
            "BAPI_PO_CHANGE", "BAPI_GOODSMVT_CREATE",
        ],
        "ap_clerk": [
            "BAPI_VENDOR_GETLIST", "BAPI_PO_GETLIST", "BAPI_PO_GETDETAIL",
            "BAPI_INCOMINGINVOICE_CREATE", "BAPI_AP_PAYMENT_POST",
        ],
        "auditor": [
            "BAPI_VENDOR_GETLIST", "BAPI_VENDOR_GETDETAIL", "BAPI_MATERIAL_GETLIST",
            "BAPI_PO_GETLIST", "BAPI_PO_GETDETAIL",
        ],
    }

    for role in role_tools:
        try:
            _toyerp_admin(base_url, admin_token, "create_role", {"role": role})
        except RuntimeError as exc:
            if "Role already exists" not in str(exc):
                raise
    for role, tools in role_tools.items():
        for tool in tools:
            _toyerp_admin(base_url, admin_token, "grant_role_tool", {"role": role, "tool": tool})

    for username, (password, role) in toyerp_users.items():
        try:
            _toyerp_admin(base_url, admin_token, "create_user", {"username": username, "password": password})
        except RuntimeError as exc:
            if "User already exists" not in str(exc):
                raise
        _toyerp_admin(base_url, admin_token, "set_user_active", {"username": username, "active": True})
        _toyerp_admin(base_url, admin_token, "assign_role", {"username": username, "role": role})

    return {username: _toyerp_login(base_url, username, password)
            for username, (password, _role) in toyerp_users.items()}


def ensure_platform_scenario(toyerp_base_url: str, toyerp_tokens: dict[str, str]) -> None:
    tenant_id = os.environ.get("PLATFORM_TENANT_ID", "65f0a1b2c3d4e5f607182901")
    role_ids = {
        "Procurement Buyer": "65f0a1b2c3d4e5f607182902",
        "AP Clerk": "65f0a1b2c3d4e5f607182903",
        "Read Only Auditor": "65f0a1b2c3d4e5f607182904",
    }
    with psycopg.connect(settings.database_url) as conn:
        conn.execute(
            """
            INSERT INTO tenants (tenant_id, name, status, policy)
            VALUES (%s, %s, 'active', %s)
            ON CONFLICT (tenant_id) DO UPDATE SET name = EXCLUDED.name, status = 'active', updated_at = now()
            """,
            (tenant_id, "Toy ERP Procurement", Jsonb({})),
        )

        permission_ids = {
            code: _stable_id("permission", tenant_id, code)
            for code in TOYERP_BAPIS
        }
        bapi_ids = {
            bapi: _stable_id("bapi", "toy-erp", bapi)
            for bapi in TOYERP_BAPIS.values()
        }

        for code, bapi in TOYERP_BAPIS.items():
            effect = "read" if code.rsplit(".", 1)[-1] in {"read", "detail"} else "write"
            conn.execute(
                """
                INSERT INTO bapi_catalog
                    (bapi_id, tenant_id, provider_key, bapi_name, description, effect, status)
                VALUES (%s, %s, 'toy-erp', %s, %s, %s, 'active')
                ON CONFLICT (tenant_id, provider_key, bapi_name) DO UPDATE
                SET description = EXCLUDED.description, effect = EXCLUDED.effect,
                    status = 'active', updated_at = now()
                """,
                (bapi_ids[bapi], tenant_id, bapi, f"Toy ERP {bapi}", effect),
            )
            conn.execute(
                """
                INSERT INTO permissions
                    (permission_id, tenant_id, permission_code, description, bapi_id, status)
                VALUES (%s, %s, %s, %s, %s, 'active')
                ON CONFLICT (tenant_id, permission_code) DO UPDATE
                SET description = EXCLUDED.description, bapi_id = EXCLUDED.bapi_id,
                    status = 'active', updated_at = now()
                """,
                (permission_ids[code], tenant_id, code, f"Allows {bapi}", bapi_ids[bapi]),
            )

        for role_name, role_id in role_ids.items():
            grants = [permission_ids[code] for code in ROLE_PERMISSIONS[role_name]]
            conn.execute(
                """
                INSERT INTO roles (role_id, tenant_id, name, description, permission_ids, status)
                VALUES (%s, %s, %s, %s, %s, 'active')
                ON CONFLICT (role_id) DO UPDATE
                  SET tenant_id = EXCLUDED.tenant_id, name = EXCLUDED.name, description = EXCLUDED.description,
                      permission_ids = EXCLUDED.permission_ids, status = 'active', updated_at = now()
                """,
                (role_id, tenant_id, role_name, f"{role_name} for Toy ERP procurement scenario", Jsonb(grants)),
            )

        user_ids: dict[str, str] = {}
        for user in USERS:
            row = conn.execute(
                """
                INSERT INTO users (user_name, email, display_name, role, status)
                VALUES (%s, %s, %s, 'user', 'active')
                ON CONFLICT (email) DO UPDATE SET user_name = EXCLUDED.user_name,
                                                   display_name = EXCLUDED.display_name,
                                                   status = 'active',
                                                   updated_at = now()
                RETURNING user_id
                """,
                (user.username, user.email, user.display_name),
            ).fetchone()
            user_id = str(row[0])
            user_ids[user.username] = user_id
            conn.execute(
                """
                INSERT INTO user_credentials (user_id, password_hash)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET password_hash = EXCLUDED.password_hash, updated_at = now()
                """,
                (user_id, hash_password(user.password)),
            )
            conn.execute(
                """
                INSERT INTO user_preferences (user_id, app_preferences, agent_preferences)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (user_id, Jsonb({}), Jsonb({})),
            )
            conn.execute(
                """
                INSERT INTO tenant_users (user_id, tenant_id, role_id, email_id, name, location, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'active')
                ON CONFLICT (user_id) DO UPDATE SET tenant_id = EXCLUDED.tenant_id,
                                                   role_id = EXCLUDED.role_id,
                                                   email_id = EXCLUDED.email_id,
                                                   name = EXCLUDED.name,
                                                   location = EXCLUDED.location,
                                                   status = 'active',
                                                   updated_at = now()
                """,
                (
                    user_id,
                    tenant_id,
                    role_ids[user.role_name],
                    user.email,
                    user.display_name,
                    "Singapore",
                ),
            )

        server_ids: dict[str, str] = {}
        for user in USERS:
            owner_id = user_ids[user.username]
            server_name = "toy-erp-procurement"
            server_row = conn.execute(
                "SELECT server_id FROM mcp_servers_catalog WHERE owner_user_id = %s AND name = %s",
                (owner_id, server_name),
            ).fetchone()
            metadata = {
                "transport": "streamable_http",
                "enabled": True,
                "auth_headers": {
                    "Authorization": f"Bearer {toyerp_tokens[user.toyerp_username]}",
                },
            }
            if server_row:
                server_id = str(server_row[0])
                conn.execute(
                    """
                    UPDATE mcp_servers_catalog
                    SET server_url = %s,
                        metadata = %s,
                        status = 'active'
                    WHERE server_id = %s
                    """,
                    (
                        f"{toyerp_base_url.rstrip('/')}/mcp",
                        Jsonb(metadata),
                        server_id,
                    ),
                )
            else:
                server_id = str(conn.execute(
                    """
                    INSERT INTO mcp_servers_catalog
                        (name, server_url, auth_type, is_global, status, owner_user_id, metadata)
                    VALUES (%s, %s, 'none', false, 'active', %s, %s)
                    RETURNING server_id
                    """,
                    (
                        server_name,
                        f"{toyerp_base_url.rstrip('/')}/mcp",
                        owner_id,
                        Jsonb(metadata),
                    ),
                ).fetchone()[0])
            server_ids[user.username] = server_id

        tenant_policy = {
            "max_query_chars": 10000,
            "requests_per_minute": 30,
            "conversation_idle_minutes": 60,
            "allowed_domains": ["procurement", "finance"],
            "permission_domains": {
                "vendor": "procurement",
                "material": "procurement",
                "purchase_order": "procurement",
                "goods_receipt": "procurement",
                "ap_invoice": "finance",
                "ap_payment": "finance",
            },
            "confirm_writes": True,
            "disabled_tools": [
                "execute_bash",
                "execute_powershell",
                "execute_python_script",
            ],
            "allowed_memory_scopes": ["USER", "AGENT"],
            "allowed_memory_types": ["workflow", "user_preference"],
            "episodic_memory_enabled": True,
            "memory_top_k": 5,
            "memory_context_tokens": 1200,
        }
        conn.execute(
            "UPDATE tenants SET policy = %s, updated_at = now() WHERE tenant_id = %s",
            (Jsonb(tenant_policy), tenant_id),
        )

    print("Platform scenario provisioned")
    print(f"tenant_id={tenant_id}")
    print("mcp_server_ids:")
    for username, server_id in server_ids.items():
        print(f"  {username}: {server_id}")
    print("Users:")
    for user in USERS:
        print(f"  {user.username} / {user.password} (role={user.role_name})")


def main() -> None:
    toyerp_base_url = os.environ.get("TOYERP_BASE_URL", "http://127.0.0.1:8000")
    admin_user = os.environ.get("TOYERP_ADMIN_USERNAME")
    admin_password = os.environ.get("TOYERP_ADMIN_PASSWORD")
    if not admin_user or not admin_password:
        raise RuntimeError("Set TOYERP_ADMIN_USERNAME and TOYERP_ADMIN_PASSWORD")

    toyerp_tokens = setup_toyerp_users(toyerp_base_url, admin_user, admin_password)
    ensure_platform_scenario(toyerp_base_url, toyerp_tokens)
    print("ToyERP users and grants provisioned")
    for username, token in toyerp_tokens.items():
        print(f"  {username} token prefix={hashlib.sha256(token.encode()).hexdigest()[:12]}")


if __name__ == "__main__":
    main()
