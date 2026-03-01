"""
API tests for Customer Intelligence fields in call summaries.
Validates that the pipeline extracts and returns:
- customer_name, detected_call_type, is_existing_customer
- sentiment_score
- qualification_status, booking_status, BANT scores
- decision_makers, urgency_signals, budget_indicators
- follow_up_required, service_requested, appointment details
"""
import pytest
import requests

from tests.api.call_processing_data import (
    STAGING_COMPANY_ID,
    REAL_CALL_ID,
)


@pytest.mark.usefixtures("api_available")
class TestCustomerIntelligence:
    """Validate Customer Intelligence fields in summary responses."""

    @pytest.fixture(scope="class")
    def summary_data(self, api_base_url, api_headers):
        """Fetch summary for a real completed call (shared across tests in class)."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/summary/{REAL_CALL_ID}",
            headers=api_headers,
            params={"include_chunks": "true"},
            timeout=15,
        )
        assert r.status_code == 200, f"Failed to fetch summary: {r.status_code}"
        return r.json()

    # ------------------------------------------------------------------
    # Qualification core fields
    # ------------------------------------------------------------------
    def test_qualification_section_exists(self, summary_data):
        """Summary must contain a qualification section."""
        assert "qualification" in summary_data, "Missing 'qualification' in summary"
        qual = summary_data["qualification"]
        assert isinstance(qual, dict)
        assert len(qual) > 0, "Qualification section is empty"

    def test_customer_name_extracted(self, summary_data):
        """Pipeline must extract a customer name from the transcript."""
        qual = summary_data["qualification"]
        assert "customer_name" in qual, "Missing customer_name"
        assert qual["customer_name"] is not None
        assert len(str(qual["customer_name"])) > 0, "customer_name is empty"

    def test_detected_call_type(self, summary_data):
        """Pipeline must detect the call type."""
        qual = summary_data["qualification"]
        assert "detected_call_type" in qual, "Missing detected_call_type"
        valid_types = ("fresh_sales", "follow_up", "confirmation", "service_call", "quote_only", "new_inquiry")
        assert qual["detected_call_type"] in valid_types, (
            f"Unexpected call type: {qual['detected_call_type']}"
        )

    def test_is_existing_customer(self, summary_data):
        """Pipeline must determine if customer is new or existing."""
        qual = summary_data["qualification"]
        assert "is_existing_customer" in qual, "Missing is_existing_customer"
        assert isinstance(qual["is_existing_customer"], bool), (
            f"is_existing_customer should be bool, got {type(qual['is_existing_customer'])}"
        )

    def test_qualification_status(self, summary_data):
        """Pipeline must assign a qualification status."""
        qual = summary_data["qualification"]
        assert "qualification_status" in qual, "Missing qualification_status"
        valid_statuses = ("hot", "warm", "cold", "unqualified")
        assert qual["qualification_status"] in valid_statuses, (
            f"Unexpected qualification_status: {qual['qualification_status']}"
        )

    def test_booking_status(self, summary_data):
        """Pipeline must assign a booking status."""
        qual = summary_data["qualification"]
        assert "booking_status" in qual, "Missing booking_status"
        valid_booking = ("booked", "not_booked", "cancelled", "rescheduled")
        assert qual["booking_status"] in valid_booking, (
            f"Unexpected booking_status: {qual['booking_status']}"
        )

    # ------------------------------------------------------------------
    # BANT Lead Scoring
    # ------------------------------------------------------------------
    def test_bant_scores_present(self, summary_data):
        """Pipeline must produce BANT scores."""
        qual = summary_data["qualification"]
        assert "bant_scores" in qual, "Missing bant_scores"
        bant = qual["bant_scores"]
        for dim in ("budget", "authority", "need", "timeline"):
            assert dim in bant, f"Missing BANT dimension: {dim}"
            assert isinstance(bant[dim], (int, float)), f"BANT {dim} should be numeric"
            assert 0.0 <= bant[dim] <= 1.0, f"BANT {dim}={bant[dim]} out of 0-1 range"

    def test_overall_bant_score(self, summary_data):
        """Pipeline must produce an overall BANT score."""
        qual = summary_data["qualification"]
        assert "overall_score" in qual, "Missing overall_score"
        score = qual["overall_score"]
        assert isinstance(score, (int, float)), "overall_score should be numeric"
        assert 0.0 <= score <= 1.0, f"overall_score={score} out of 0-1 range"

    # ------------------------------------------------------------------
    # Sentiment
    # ------------------------------------------------------------------
    def test_sentiment_score(self, summary_data):
        """Summary must include a sentiment score."""
        summary_obj = summary_data.get("summary", {})
        assert "sentiment_score" in summary_obj, "Missing sentiment_score in summary"
        score = summary_obj["sentiment_score"]
        assert isinstance(score, (int, float)), "sentiment_score should be numeric"
        assert 0.0 <= score <= 1.0, f"sentiment_score={score} out of 0-1 range"

    # ------------------------------------------------------------------
    # Decision makers & signals
    # ------------------------------------------------------------------
    def test_decision_makers(self, summary_data):
        """Pipeline should extract decision makers when present."""
        qual = summary_data["qualification"]
        assert "decision_makers" in qual, "Missing decision_makers"
        assert isinstance(qual["decision_makers"], list)

    def test_urgency_signals(self, summary_data):
        """Pipeline should extract urgency signals when present."""
        qual = summary_data["qualification"]
        assert "urgency_signals" in qual, "Missing urgency_signals"
        assert isinstance(qual["urgency_signals"], list)

    def test_budget_indicators(self, summary_data):
        """Pipeline should extract budget indicators when present."""
        qual = summary_data["qualification"]
        assert "budget_indicators" in qual, "Missing budget_indicators"
        assert isinstance(qual["budget_indicators"], list)

    # ------------------------------------------------------------------
    # Follow-up & service
    # ------------------------------------------------------------------
    def test_follow_up_fields(self, summary_data):
        """Pipeline must indicate if follow-up is required."""
        qual = summary_data["qualification"]
        assert "follow_up_required" in qual, "Missing follow_up_required"
        assert isinstance(qual["follow_up_required"], bool)
        if qual["follow_up_required"]:
            assert "follow_up_reason" in qual, "follow_up_required=true but no follow_up_reason"
            assert len(qual["follow_up_reason"]) > 0, "follow_up_reason is empty"

    def test_service_requested(self, summary_data):
        """Pipeline should extract the service requested."""
        qual = summary_data["qualification"]
        assert "service_requested" in qual, "Missing service_requested"

    def test_appointment_fields(self, summary_data):
        """Pipeline must include appointment tracking fields."""
        qual = summary_data["qualification"]
        assert "appointment_confirmed" in qual, "Missing appointment_confirmed"
        assert isinstance(qual["appointment_confirmed"], bool)
        assert "appointment_date" in qual, "Missing appointment_date"

    def test_confidence_score(self, summary_data):
        """Pipeline must provide an extraction confidence score."""
        qual = summary_data["qualification"]
        assert "confidence_score" in qual, "Missing confidence_score"
        score = qual["confidence_score"]
        assert isinstance(score, (int, float)), "confidence_score should be numeric"
        assert 0.0 <= score <= 1.0, f"confidence_score={score} out of 0-1 range"

    # ------------------------------------------------------------------
    # Call outcome
    # ------------------------------------------------------------------
    def test_call_outcome_category(self, summary_data):
        """Pipeline should classify the call outcome."""
        qual = summary_data["qualification"]
        assert "call_outcome_category" in qual, "Missing call_outcome_category"
        assert qual["call_outcome_category"] is not None
        assert len(str(qual["call_outcome_category"])) > 0

    # ------------------------------------------------------------------
    # Service Address & Geolocation
    # ------------------------------------------------------------------
    def test_service_address_structured(self, summary_data):
        """Pipeline must return a structured address object."""
        qual = summary_data["qualification"]
        assert "service_address_structured" in qual, "Missing service_address_structured"
        addr = qual["service_address_structured"]
        assert isinstance(addr, dict), "service_address_structured should be a dict"
        for field in ("line1", "city", "state", "postal_code", "country"):
            assert field in addr, f"Missing address field: {field}"

    def test_address_confidence_score(self, summary_data):
        """Pipeline must return address extraction confidence."""
        qual = summary_data["qualification"]
        assert "address_confidence" in qual, "Missing address_confidence"
        score = qual["address_confidence"]
        assert isinstance(score, (int, float)), "address_confidence should be numeric"
        assert 0.0 <= score <= 1.0, f"address_confidence={score} out of 0-1 range"

    # ------------------------------------------------------------------
    # Appointment Details (Extractor Call 2)
    # ------------------------------------------------------------------
    def test_appointment_type(self, summary_data):
        """Pipeline must detect appointment type (in_person, phone, virtual)."""
        qual = summary_data["qualification"]
        assert "appointment_type" in qual, "Missing appointment_type"

    def test_appointment_timezone(self, summary_data):
        """Pipeline must include appointment timezone."""
        qual = summary_data["qualification"]
        assert "appointment_timezone" in qual, "Missing appointment_timezone"

    def test_appointment_time_confidence(self, summary_data):
        """Pipeline must include confidence score for appointment time extraction."""
        qual = summary_data["qualification"]
        assert "appointment_time_confidence" in qual, "Missing appointment_time_confidence"
        score = qual["appointment_time_confidence"]
        assert isinstance(score, (int, float)), "appointment_time_confidence should be numeric"
        assert 0.0 <= score <= 1.0, f"appointment_time_confidence={score} out of 0-1 range"

    def test_appointment_intent(self, summary_data):
        """Pipeline must classify appointment intent (new, reschedule, cancel)."""
        qual = summary_data["qualification"]
        assert "appointment_intent" in qual, "Missing appointment_intent"

    # ------------------------------------------------------------------
    # Enhanced Validation — customer_name_confidence
    # ------------------------------------------------------------------
    def test_customer_name_confidence(self, summary_data):
        """Pipeline must provide confidence score for customer name extraction.
        This validates the anti-confusion logic (prevents rep/customer name swap)."""
        qual = summary_data["qualification"]
        assert "customer_name_confidence" in qual, "Missing customer_name_confidence"
        score = qual["customer_name_confidence"]
        assert isinstance(score, (int, float)), "customer_name_confidence should be numeric"
        assert 0.0 <= score <= 1.0, f"customer_name_confidence={score} out of 0-1 range"

    # ------------------------------------------------------------------
    # Property Details (Architecture doc: Extractor Call 4)
    # NOTE: These fields are documented but NOT returned by the staging API.
    # Tests are marked xfail to document the gap without failing the suite.
    # ------------------------------------------------------------------
    @pytest.mark.xfail(reason="Property details not yet returned by staging API — test gap")
    def test_property_roof_type(self, summary_data):
        """Pipeline should extract roof type from home services calls."""
        qual = summary_data["qualification"]
        assert "roof_type" in qual, "Missing roof_type (documented in architecture but not in API response)"

    @pytest.mark.xfail(reason="Property details not yet returned by staging API — test gap")
    def test_property_roof_age(self, summary_data):
        """Pipeline should extract roof age."""
        qual = summary_data["qualification"]
        assert "roof_age" in qual, "Missing roof_age"

    @pytest.mark.xfail(reason="Property details not yet returned by staging API — test gap")
    def test_property_hoa_status(self, summary_data):
        """Pipeline should extract HOA status."""
        qual = summary_data["qualification"]
        assert "hoa_status" in qual, "Missing hoa_status"

    @pytest.mark.xfail(reason="Property details not yet returned by staging API — test gap")
    def test_property_pets_on_property(self, summary_data):
        """Pipeline should extract pets on property."""
        qual = summary_data["qualification"]
        assert "pets_on_property" in qual, "Missing pets_on_property"

    @pytest.mark.xfail(reason="Property details not yet returned by staging API — test gap")
    def test_property_solar_panels(self, summary_data):
        """Pipeline should extract solar panel installation status."""
        qual = summary_data["qualification"]
        assert "solar_panels" in qual, "Missing solar_panels"

    @pytest.mark.xfail(reason="Property details not yet returned by staging API — test gap")
    def test_property_access_notes(self, summary_data):
        """Pipeline should extract property access notes."""
        qual = summary_data["qualification"]
        assert "access_notes" in qual, "Missing access_notes"


@pytest.mark.usefixtures("api_available")
class TestCustomerIntelligenceAcrossCalls:
    """Validate Customer Intelligence consistency across multiple calls."""

    def test_all_completed_calls_have_qualification(self, api_base_url, api_headers):
        """Every completed call should have a qualification section with core fields."""
        # Fetch call list
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=api_headers,
            params={"company_id": STAGING_COMPANY_ID, "limit": 10, "sort_by": "call_date", "sort_order": "desc"},
            timeout=15,
        )
        assert r.status_code == 200
        calls = r.json().get("calls", [])
        completed = [c for c in calls if c.get("status") == "completed"]
        assert len(completed) > 0, "No completed calls found"

        checked = 0
        for call in completed[:5]:  # Check up to 5 calls
            sr = requests.get(
                f"{api_base_url}/api/v1/call-processing/summary/{call['call_id']}",
                headers=api_headers,
                timeout=15,
            )
            if sr.status_code != 200:
                continue
            data = sr.json()
            qual = data.get("qualification", {})
            assert "customer_name" in qual, f"Call {call['call_id']}: missing customer_name"
            assert "detected_call_type" in qual, f"Call {call['call_id']}: missing detected_call_type"
            assert "qualification_status" in qual, f"Call {call['call_id']}: missing qualification_status"
            assert "bant_scores" in qual, f"Call {call['call_id']}: missing bant_scores"
            checked += 1

        assert checked >= 3, f"Only verified {checked} calls, expected at least 3"
