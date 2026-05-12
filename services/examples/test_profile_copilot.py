from fastapi.testclient import TestClient

from services.api import server
from services.copilot.draft_generator import ProfileDraftGenerator
from services.copilot.draft_validator import ProfileDraftValidator
from services.copilot.guardrails import CopilotGuardrails
from services.copilot.profile_context import ProfileContextProvider
from services.copilot.router import reset_profile_copilot_service
from services.copilot.schemas import DraftGenerationResult
from services.copilot.service import ProfileCopilotService
from services.copilot.session_store import InMemoryCopilotSessionStore
from services.profiles.manager import (
    ADMIN_USER_ID,
    ProfileCreateRequest,
    ProfileManager,
    RedisProfileStateStore,
)
from services.storage.local import LocalStorageProvider


VALID_PROFILE_YAML = """
description: finance report profile
highlight_config:
  extraction_prompt: |
    Extract company_name, revenue, profit, yoy_change, and risk_note from finance reports.
  category_colors:
    - name: company_name
      color: "#2ecc71"
      description: Company name
    - name: revenue
      color: "#3498db"
      description: Revenue metric
  examples:
    - text: "ACME revenue 120 million profit 30 million"
      extractions:
        - class: company_name
          text: "ACME"
        - class: revenue
          text: "120 million"
"""


class FakeRedis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def delete(self, key):
        self.values.pop(key, None)


class FakeDraftGenerator(ProfileDraftGenerator):
    def generate(self, request):
        return DraftGenerationResult(
            assistant_message="已生成财务报告 Profile 草稿。",
            draft_yaml=VALID_PROFILE_YAML,
        )


def build_manager(tmp_path):
    return ProfileManager(
        storage_provider=LocalStorageProvider(root_dir=str(tmp_path / "storage")),
        active_state_store=RedisProfileStateStore(FakeRedis()),
        seed_dir=tmp_path / "seed",
        enable_seed_import=False,
    )


def build_service(manager):
    return ProfileCopilotService(
        profile_manager=manager,
        session_store=InMemoryCopilotSessionStore(),
        draft_generator=FakeDraftGenerator(),
    )


def test_session_store_and_guardrails(tmp_path):
    service = build_service(build_manager(tmp_path))
    session = service.create_session(ADMIN_USER_ID)

    rejected = service.process_message(session["session_id"], ADMIN_USER_ID, "帮我执行 powershell 命令")

    assert rejected["rejected"] is True
    assert "只能帮助" in rejected["assistant_message"]


def test_profile_context_provider_extracts_profile_summary(tmp_path):
    manager = build_manager(tmp_path)
    manager.create_profile(
        ADMIN_USER_ID,
        ProfileCreateRequest(content=VALID_PROFILE_YAML, filename="finance.yaml"),
    )

    context = ProfileContextProvider(manager).retrieve(ADMIN_USER_ID, "财务 revenue 高亮 profile")

    assert context
    assert context[0].profile_id == "finance"
    assert "revenue" in context[0].summary


def test_draft_validator_accepts_valid_and_rejects_invalid_yaml():
    validator = ProfileDraftValidator()

    valid = validator.validate(VALID_PROFILE_YAML)
    invalid = validator.validate("highlight_config: [")
    invalid_rule_list = validator.validate(
        """
description: resume profile
highlight_config:
  - name: name
    pattern: "姓名"
"""
    )

    assert valid.valid is True
    assert invalid.valid is False
    assert invalid.errors
    assert invalid_rule_list.valid is False
    assert "不能是列表" in invalid_rule_list.errors[0]


def test_draft_generator_prompt_includes_fusion_mark_config_skill():
    generator = ProfileDraftGenerator()

    messages = generator._build_messages(
        type(
            "Request",
            (),
            {
                "user_message": "生成简历高亮 profile",
                "current_draft_yaml": "",
                "referenced_profiles": [],
            },
        )()
    )

    system_prompt = messages[0]["content"]
    assert "Fusion-Mark Config" in system_prompt
    assert "Current YAML Shape" in system_prompt
    assert "highlight_config MUST be a mapping/object" in system_prompt
    assert "Authoritative profile template" in system_prompt


def test_profile_copilot_api_session_message_and_validate(monkeypatch, tmp_path):
    service = build_service(build_manager(tmp_path))
    reset_profile_copilot_service()

    import services.copilot.router as copilot_router

    monkeypatch.setattr(copilot_router, "_profile_copilot_service", service)
    monkeypatch.setattr(copilot_router, "get_current_user_id", lambda: ADMIN_USER_ID)

    client = TestClient(server.app)

    created = client.post("/api/v1/profile-copilot/sessions")
    assert created.status_code == 200
    session_id = created.json()["session_id"]

    message = client.post(
        f"/api/v1/profile-copilot/sessions/{session_id}/messages",
        json={"message": "生成一个财务报告高亮 profile，抽取 revenue 和 profit"},
    )
    assert message.status_code == 200
    payload = message.json()
    assert payload["rejected"] is False
    assert payload["validation"]["valid"] is True
    assert "highlight_config" in payload["draft_yaml"]

    validation = client.post(
        f"/api/v1/profile-copilot/sessions/{session_id}/validate",
        json={"draft_yaml": "highlight_config: ["},
    )
    assert validation.status_code == 200
    assert validation.json()["validation"]["valid"] is False
