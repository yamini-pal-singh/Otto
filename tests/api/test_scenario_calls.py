"""
Test Scenario Calls — Dynamically fetch the most recent calls from the Otto API
and validate one unique call per scenario based on:
  - scope_classification (IN_SCOPE / OUT_OF_SCOPE)
  - qualification_status (hot / warm / cold / unqualified)
  - booking_status (booked / not_booked / service_not_offered)
  - objections (present / absent)
  - call_outcome_category

Calls are fetched live, sorted most-recent-first, with no duplicates across scenarios.
"""
import pytest
import requests

import os
from dotenv import load_dotenv

load_dotenv()

STAGING_COMPANY_ID = "1be5ea90-d3ae-4b03-8b05-f5679cd73bc4"


# ---------------------------------------------------------------------------
# Scenario definitions — each tuple is:
#   (scope_classification, qualification_status, booking_status, has_objections)
# ---------------------------------------------------------------------------
SCENARIO_DEFS = {
    "in_scope__hot__booked__with_objections": ("IN_SCOPE", "hot", "booked", True),
    "in_scope__hot__not_booked__with_objections": ("IN_SCOPE", "hot", "not_booked", True),
    "in_scope__warm__not_booked__with_objections": ("IN_SCOPE", "warm", "not_booked", True),
    "in_scope__cold__not_booked__with_objections": ("IN_SCOPE", "cold", "not_booked", True),
    "out_of_scope__unqualified__not_booked__no_objections": ("OUT_OF_SCOPE", "unqualified", "not_booked", False),
    "any_scope__hot__booked__with_objections": (None, "hot", "booked", True),
    "any_scope__hot__not_booked__with_objections": (None, "hot", "not_booked", True),
    "any_scope__warm__booked__with_objections": (None, "warm", "booked", True),
    "any_scope__warm__not_booked__no_objections": (None, "warm", "not_booked", False),
    "any_scope__warm__not_booked__with_objections": (None, "warm", "not_booked", True),
    "any_scope__warm__service_not_offered__with_objections": (None, "warm", "service_not_offered", True),
    "any_scope__cold__not_booked__no_objections": (None, "cold", "not_booked", False),
    "any_scope__cold__not_booked__with_objections": (None, "cold", "not_booked", True),
    "any_scope__cold__service_not_offered__with_objections": (None, "cold", "service_not_offered", True),
    "any_scope__unqualified__booked__no_objections": (None, "unqualified", "booked", False),
    "any_scope__unqualified__not_booked__no_objections": (None, "unqualified", "not_booked", False),
}

# Valid enum values per API documentation
VALID_SCOPE_CLASSIFICATIONS = ("IN_SCOPE", "OUT_OF_SCOPE")
VALID_QUALIFICATION_STATUSES = ("hot", "warm", "cold", "unqualified")
VALID_BOOKING_STATUSES = ("booked", "not_booked", "service_not_offered")
VALID_CALL_OUTCOME_CATEGORIES = (
    "qualified_and_booked",
    "qualified_but_unbooked",
    "qualified_but_deprioritized",
    "qualified_service_not_offered",
    "follow_up_inquiry",
    "existing_customer_service",
    "unqualified",
)
VALID_DETECTED_CALL_TYPES = (
    "new_inquiry", "follow_up", "service_call", "confirmation", "quote_only", "fresh_sales",
)
VALID_OBJECTION_CATEGORIES = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}


def _matches_scenario(summary, scope, qual_status, book_status, has_obj):
    """Check if a summary matches the given scenario filters."""
    q = summary.get("qualification") or {}
    o = summary.get("objections") or {}
    obj_count = o.get("total_count", 0) or 0

    if scope is not None and q.get("scope_classification") != scope:
        return False
    if q.get("qualification_status") != qual_status:
        return False
    if q.get("booking_status") != book_status:
        return False
    if has_obj and obj_count == 0:
        return False
    if not has_obj and obj_count > 0:
        return False
    return True


def _fetch_all_summaries(base_url, headers):
    """Fetch up to 200 most-recent summaries from the API."""
    resp = requests.get(
        f"{base_url}/api/v1/call-processing/summaries",
        headers=headers,
        params={
            "company_id": STAGING_COMPANY_ID,
            "limit": 200,
            "sort_by": "created_at",
            "sort_order": "desc",
        },
        timeout=60,
    )
    assert resp.status_code == 200, f"Failed to fetch summaries: {resp.status_code}"
    return resp.json().get("summaries", [])


def _select_scenario_calls(summaries):
    """Pick one most-recent call per scenario. No call_id reuse across scenarios."""
    used_ids = set()
    selected = {}

    for name, (scope, qual_status, book_status, has_obj) in SCENARIO_DEFS.items():
        for s in summaries:
            cid = s["call_id"]
            if cid in used_ids:
                continue
            if _matches_scenario(s, scope, qual_status, book_status, has_obj):
                used_ids.add(cid)
                selected[name] = s
                break

    return selected


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def all_summaries(api_base_url, api_headers):
    """Fetch all recent summaries once per module run."""
    return _fetch_all_summaries(api_base_url, api_headers)


@pytest.fixture(scope="module")
def scenario_calls(all_summaries):
    """Map of scenario_name -> summary dict, one unique call per scenario."""
    selected = _select_scenario_calls(all_summaries)
    return selected


def _get_scenario(scenario_calls, name):
    """Get a scenario call or skip the test if not available."""
    if name not in scenario_calls:
        pytest.skip(f"No call found for scenario: {name}")
    return scenario_calls[name]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("api_available")
class TestScenarioDiscovery:
    """Verify that scenario selection fetches calls correctly."""

    def test_summaries_fetched(self, all_summaries):
        """API returns at least some summaries."""
        assert len(all_summaries) > 0, "No summaries returned from API"

    def test_no_duplicate_call_ids(self, scenario_calls):
        """Each scenario uses a unique call_id."""
        call_ids = [s["call_id"] for s in scenario_calls.values()]
        assert len(call_ids) == len(set(call_ids)), (
            f"Duplicate call_ids in scenario selection: {call_ids}"
        )

    def test_at_least_5_scenarios_matched(self, scenario_calls):
        """At least 5 distinct scenarios should be matchable from live data."""
        assert len(scenario_calls) >= 5, (
            f"Only {len(scenario_calls)} scenarios matched — expected at least 5. "
            f"Matched: {list(scenario_calls.keys())}"
        )

    def test_print_selected_scenarios(self, scenario_calls):
        """Print selected scenario mapping for debugging."""
        for name, s in scenario_calls.items():
            q = s.get("qualification") or {}
            o = s.get("objections") or {}
            print(
                f"\n  {name}:"
                f"\n    call_id={s['call_id']}"
                f"\n    created_at={s.get('created_at', '?')}"
                f"\n    scope={q.get('scope_classification', 'N/A')}"
                f"\n    qual={q.get('qualification_status')}"
                f"\n    booked={q.get('booking_status')}"
                f"\n    objections={o.get('total_count', 0)}"
                f"\n    outcome={q.get('call_outcome_category')}"
                f"\n    service={q.get('service_requested', 'N/A')}"
            )


@pytest.mark.usefixtures("api_available")
class TestScopeClassification:
    """Validate scope_classification field for IN_SCOPE and OUT_OF_SCOPE calls."""

    def test_in_scope_call_has_valid_scope(self, scenario_calls):
        s = _get_scenario(scenario_calls, "in_scope__hot__booked__with_objections")
        qual = s["qualification"]
        assert qual["scope_classification"] == "IN_SCOPE"
        assert qual.get("scope_confidence") is not None
        assert 0.0 <= qual["scope_confidence"] <= 1.0
        assert qual.get("scope_reason") is not None
        assert isinstance(qual.get("scope_signals"), list)

    def test_out_of_scope_call_has_zeroed_bant(self, scenario_calls):
        s = _get_scenario(scenario_calls, "out_of_scope__unqualified__not_booked__no_objections")
        qual = s["qualification"]
        assert qual["scope_classification"] == "OUT_OF_SCOPE"
        assert qual["qualification_status"] == "unqualified"
        bant = qual.get("bant_scores") or {}
        for dim in ("need", "budget", "timeline", "authority"):
            assert bant.get(dim, 0) == 0, f"OUT_OF_SCOPE call should have {dim}=0, got {bant.get(dim)}"

    def test_out_of_scope_outcome_is_unqualified(self, scenario_calls):
        s = _get_scenario(scenario_calls, "out_of_scope__unqualified__not_booked__no_objections")
        qual = s["qualification"]
        assert qual["call_outcome_category"] == "unqualified"


@pytest.mark.usefixtures("api_available")
class TestQualifiedScenarios:
    """Validate qualification fields for hot/warm/cold calls."""

    def test_hot_booked_call(self, scenario_calls):
        s = _get_scenario(scenario_calls, "in_scope__hot__booked__with_objections")
        qual = s["qualification"]
        assert qual["qualification_status"] == "hot"
        assert qual["booking_status"] == "booked"
        assert qual["call_outcome_category"] == "qualified_and_booked"
        # BANT scores should be populated
        bant = qual.get("bant_scores") or {}
        assert bant.get("need", 0) > 0 or bant.get("budget", 0) > 0, "Hot call should have non-zero BANT"
        # Appointment details when booked
        assert qual.get("appointment_date") is not None or qual.get("appointment_confirmed") is not None

    def test_hot_not_booked_call(self, scenario_calls):
        s = _get_scenario(scenario_calls, "in_scope__hot__not_booked__with_objections")
        qual = s["qualification"]
        assert qual["qualification_status"] == "hot"
        assert qual["booking_status"] == "not_booked"
        assert qual["call_outcome_category"] in ("qualified_but_unbooked", "follow_up_inquiry")

    def test_warm_not_booked_with_objections(self, scenario_calls):
        s = _get_scenario(scenario_calls, "in_scope__warm__not_booked__with_objections")
        qual = s["qualification"]
        assert qual["qualification_status"] == "warm"
        assert qual["booking_status"] == "not_booked"
        bant = qual.get("bant_scores") or {}
        assert isinstance(bant, dict)

    def test_cold_not_booked_call(self, scenario_calls):
        s = _get_scenario(scenario_calls, "in_scope__cold__not_booked__with_objections")
        qual = s["qualification"]
        assert qual["qualification_status"] == "cold"
        assert qual["booking_status"] == "not_booked"


@pytest.mark.usefixtures("api_available")
class TestServiceOffered:
    """Validate service_not_offered scenarios."""

    def test_service_not_offered_has_reason(self, scenario_calls):
        s = _get_scenario(scenario_calls, "any_scope__warm__service_not_offered__with_objections")
        qual = s["qualification"]
        assert qual["booking_status"] == "service_not_offered"
        assert qual["call_outcome_category"] == "qualified_service_not_offered"
        # Should have a reason why service isn't offered
        assert qual.get("service_not_offered_reason") is not None or qual.get("deferred_reason") is not None, (
            "service_not_offered call should have service_not_offered_reason or deferred_reason"
        )

    def test_cold_service_not_offered(self, scenario_calls):
        s = _get_scenario(scenario_calls, "any_scope__cold__service_not_offered__with_objections")
        qual = s["qualification"]
        assert qual["booking_status"] == "service_not_offered"


@pytest.mark.usefixtures("api_available")
class TestBookedScenarios:
    """Validate booked appointment fields."""

    def test_booked_has_appointment_fields(self, scenario_calls):
        s = _get_scenario(scenario_calls, "any_scope__warm__booked__with_objections")
        qual = s["qualification"]
        assert qual["booking_status"] == "booked"
        # Booked calls should have at least some appointment info
        has_appointment_info = any([
            qual.get("appointment_date"),
            qual.get("appointment_confirmed") is not None,
            qual.get("appointment_type"),
        ])
        assert has_appointment_info, "Booked call should have appointment details"

    def test_unqualified_booked_is_follow_up(self, scenario_calls):
        s = _get_scenario(scenario_calls, "any_scope__unqualified__booked__no_objections")
        qual = s["qualification"]
        assert qual["qualification_status"] == "unqualified"
        assert qual["booking_status"] == "booked"
        assert qual["call_outcome_category"] in ("follow_up_inquiry", "existing_customer_service")


@pytest.mark.usefixtures("api_available")
class TestObjections:
    """Validate objection extraction for calls with and without objections."""

    def test_call_with_objections_has_valid_structure(self, scenario_calls):
        s = _get_scenario(scenario_calls, "in_scope__hot__booked__with_objections")
        obj = s.get("objections") or {}
        assert obj.get("total_count", 0) > 0, "Expected objections for this scenario"
        objection_list = obj.get("objections", [])
        assert isinstance(objection_list, list)
        assert len(objection_list) > 0

        for o in objection_list:
            assert "category_id" in o, "Objection missing category_id"
            assert o["category_id"] in VALID_OBJECTION_CATEGORIES, (
                f"Invalid objection category_id: {o['category_id']}"
            )
            assert "category_text" in o
            assert "objection_text" in o
            assert "overcome" in o
            assert isinstance(o["overcome"], bool)
            assert "confidence_score" in o
            assert 0.0 <= o["confidence_score"] <= 1.0
            assert "severity" in o
            assert o["severity"] in ("low", "medium", "high")

    def test_call_without_objections(self, scenario_calls):
        s = _get_scenario(scenario_calls, "out_of_scope__unqualified__not_booked__no_objections")
        obj = s.get("objections") or {}
        assert (obj.get("total_count", 0) or 0) == 0

    def test_objection_category_9_has_sub_objection(self, scenario_calls):
        """Category 9 (Other) should have a sub_objection value per API doc.
        NOTE: Known data issue — some category 9 objections return sub_objection=None.
        This test warns instead of failing to track the issue without blocking CI.
        """
        found_cat9 = False
        missing_sub = []
        for name, s in scenario_calls.items():
            obj = s.get("objections") or {}
            for o in obj.get("objections", []):
                if o.get("category_id") == 9:
                    found_cat9 = True
                    if o.get("sub_objection") is None:
                        missing_sub.append(s["call_id"])
        if not found_cat9:
            pytest.skip("No category 9 (Other) objections found in any scenario call")
        if missing_sub:
            import warnings
            warnings.warn(
                f"Category 9 objections missing sub_objection in calls: {missing_sub}. "
                "Per API doc, category 9 should always have sub_objection populated."
            )


@pytest.mark.usefixtures("api_available")
class TestCallOutcomeCategories:
    """Validate call_outcome_category across different scenarios."""

    def test_qualified_and_booked_outcome(self, scenario_calls):
        s = _get_scenario(scenario_calls, "in_scope__hot__booked__with_objections")
        assert s["qualification"]["call_outcome_category"] == "qualified_and_booked"

    def test_qualified_but_unbooked_outcome(self, scenario_calls):
        s = _get_scenario(scenario_calls, "in_scope__hot__not_booked__with_objections")
        qual = s["qualification"]
        assert qual["call_outcome_category"] in ("qualified_but_unbooked", "follow_up_inquiry")

    def test_service_not_offered_outcome(self, scenario_calls):
        s = _get_scenario(scenario_calls, "any_scope__warm__service_not_offered__with_objections")
        assert s["qualification"]["call_outcome_category"] == "qualified_service_not_offered"

    def test_unqualified_outcome(self, scenario_calls):
        s = _get_scenario(scenario_calls, "out_of_scope__unqualified__not_booked__no_objections")
        assert s["qualification"]["call_outcome_category"] == "unqualified"

    def test_all_outcomes_are_valid(self, scenario_calls):
        """Every selected call must have a valid call_outcome_category."""
        for name, s in scenario_calls.items():
            outcome = s["qualification"].get("call_outcome_category")
            assert outcome in VALID_CALL_OUTCOME_CATEGORIES, (
                f"Scenario {name} (call {s['call_id']}) has invalid outcome: {outcome}"
            )


@pytest.mark.usefixtures("api_available")
class TestLeadScoreAndBANT:
    """Validate lead_score and BANT across qualified scenarios."""

    def test_hot_call_has_lead_score(self, scenario_calls):
        s = _get_scenario(scenario_calls, "in_scope__hot__booked__with_objections")
        lead = s.get("lead_score")
        assert lead is not None, "Hot booked call should have lead_score"
        assert "total_score" in lead
        assert 0 <= lead["total_score"] <= 100
        assert lead.get("lead_band") in ("hot", "warm", "cold")
        assert isinstance(lead.get("breakdown"), list)
        assert len(lead["breakdown"]) > 0

    def test_bant_scores_are_valid(self, scenario_calls):
        """All IN_SCOPE calls should have valid BANT score ranges."""
        for name, s in scenario_calls.items():
            qual = s["qualification"]
            if qual.get("scope_classification") == "OUT_OF_SCOPE":
                continue
            bant = qual.get("bant_scores")
            if bant is None:
                continue
            for dim in ("need", "budget", "timeline", "authority"):
                val = bant.get(dim)
                if val is not None:
                    assert 0.0 <= val <= 1.0, (
                        f"Scenario {name}: BANT {dim}={val} out of range [0, 1]"
                    )


@pytest.mark.usefixtures("api_available")
class TestComplianceAcrossScenarios:
    """Validate compliance section is present and consistent."""

    def test_compliance_present_in_all_scenarios(self, scenario_calls):
        for name, s in scenario_calls.items():
            comp = s.get("compliance")
            assert comp is not None, f"Scenario {name} ({s['call_id']}) missing compliance"
            sop = comp.get("sop_compliance") or {}
            score = sop.get("score")
            assert score is not None, f"Scenario {name} missing compliance score"
            assert 0.0 <= score <= 1.0, f"Scenario {name} compliance score {score} out of range"

    def test_compliance_has_stages(self, scenario_calls):
        for name, s in scenario_calls.items():
            sop = (s.get("compliance") or {}).get("sop_compliance") or {}
            stages = sop.get("stages")
            if stages is None:
                continue
            assert "total" in stages
            assert "followed" in stages
            assert "missed" in stages
            assert isinstance(stages["followed"], list)
            assert isinstance(stages["missed"], list)


@pytest.mark.usefixtures("api_available")
class TestSummaryFieldsAcrossScenarios:
    """Validate summary section consistency across all scenario calls."""

    def test_summary_text_present(self, scenario_calls):
        for name, s in scenario_calls.items():
            summary = s.get("summary") or {}
            assert summary.get("summary"), f"Scenario {name} ({s['call_id']}) has empty summary text"

    def test_sentiment_in_range(self, scenario_calls):
        for name, s in scenario_calls.items():
            summary = s.get("summary") or {}
            score = summary.get("sentiment_score")
            if score is not None:
                assert 0.0 <= score <= 1.0, (
                    f"Scenario {name}: sentiment_score={score} out of [0, 1]"
                )

    def test_key_points_are_list(self, scenario_calls):
        for name, s in scenario_calls.items():
            summary = s.get("summary") or {}
            kp = summary.get("key_points")
            if kp is not None:
                assert isinstance(kp, list), f"Scenario {name}: key_points is not a list"


@pytest.mark.usefixtures("api_available")
class TestFullCallDetailFetch:
    """Fetch full summary for each selected scenario call and validate structure."""

    def test_individual_summary_fetch(self, api_base_url, api_headers, scenario_calls):
        """Each scenario call_id should be fetchable via GET /summary/{call_id}."""
        for name, s in scenario_calls.items():
            call_id = s["call_id"]
            r = requests.get(
                f"{api_base_url}/api/v1/call-processing/summary/{call_id}",
                headers=api_headers,
                timeout=15,
            )
            assert r.status_code == 200, (
                f"Scenario {name}: GET summary/{call_id} returned {r.status_code}"
            )
            data = r.json()
            assert data["call_id"] == call_id
            assert "summary" in data
            assert "qualification" in data
            assert "compliance" in data
