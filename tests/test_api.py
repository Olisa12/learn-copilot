"""
Tests for the Mergington High School Activities API.
Uses AAA (Arrange-Act-Assert) pattern for test structure.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        # Arrange: No setup needed, activities are predefined in app
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_activities_have_required_fields(self, client):
        # Arrange
        expected_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity in activities.items():
            assert expected_fields.issubset(activity.keys())
            assert isinstance(activity["participants"], list)
    
    def test_activities_have_valid_participant_data(self, client):
        # Arrange
        expected_participants_in_chess = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        chess_participants = data["Chess Club"]["participants"]
        
        # Assert
        assert response.status_code == 200
        assert set(expected_participants_in_chess) == set(chess_participants)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client):
        # Arrange
        activity_name = "Chess%20Club"
        new_email = "newstudent123@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={new_email}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert new_email.replace("%20", " ") in data["message"] or new_email in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client):
        # Arrange
        activity_name = "Programming%20Class"
        test_email = "newprogrammer@mergington.edu"
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        response = client.get("/activities")
        
        # Assert
        activities = response.json()
        assert test_email in activities["Programming Class"]["participants"]
    
    def test_signup_duplicate_fails(self, client):
        # Arrange
        activity_name = "Science%20Club"
        duplicate_email = "duplicate999@mergington.edu"
        
        # Act - First signup
        first_response = client.post(f"/activities/{activity_name}/signup?email={duplicate_email}")
        # Act - Second signup with same email
        second_response = client.post(f"/activities/{activity_name}/signup?email={duplicate_email}")
        
        # Assert
        assert first_response.status_code == 200
        assert second_response.status_code == 400
        data = second_response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        # Arrange
        nonexistent_activity = "Nonexistent%20Club"
        test_email = "test@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{nonexistent_activity}/signup?email={test_email}")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_increments_participant_count(self, client):
        # Arrange
        activity_name = "Basketball%20Team"
        test_email = "newbasketballer@mergington.edu"
        response_before = client.get("/activities")
        count_before = len(response_before.json()["Basketball Team"]["participants"])
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        response_after = client.get("/activities")
        
        # Assert
        count_after = len(response_after.json()["Basketball Team"]["participants"])
        assert count_after == count_before + 1


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client):
        # Arrange
        activity_name = "Art%20Club"
        test_email = "artist@mergington.edu"
        # First sign up
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        
        # Act
        response = client.delete(f"/activities/{activity_name}/unregister?email={test_email}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        assert test_email in data["message"]
    
    def test_unregister_removes_participant_from_list(self, client):
        # Arrange
        activity_name = "Drama%20Club"
        test_email = "actor@mergington.edu"
        # Sign up first
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        
        # Act
        client.delete(f"/activities/{activity_name}/unregister?email={test_email}")
        response = client.get("/activities")
        
        # Assert
        activities = response.json()
        assert test_email not in activities["Drama Club"]["participants"]
    
    def test_unregister_decrements_participant_count(self, client):
        # Arrange
        activity_name = "Soccer%20Club"
        test_email = "soccer@mergington.edu"
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        response_before = client.get("/activities")
        count_before = len(response_before.json()["Soccer Club"]["participants"])
        
        # Act
        client.delete(f"/activities/{activity_name}/unregister?email={test_email}")
        response_after = client.get("/activities")
        
        # Assert
        count_after = len(response_after.json()["Soccer Club"]["participants"])
        assert count_after == count_before - 1
    
    def test_unregister_nonexistent_activity_returns_404(self, client):
        # Arrange
        nonexistent_activity = "Fake%20Club"
        test_email = "test@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{nonexistent_activity}/unregister?email={test_email}")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_nonexistent_participant_returns_404(self, client):
        # Arrange
        activity_name = "Debate%20Club"
        nonexistent_email = "notexist@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/unregister?email={nonexistent_email}")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestRootEndpoint:
    """Tests for GET / endpoint."""
    
    def test_root_redirects_to_static_index(self, client):
        # Arrange
        
        # Act
        response = client.get("/", follow_redirects=True)
        
        # Assert
        assert response.status_code == 200
        assert "Mergington High School" in response.text or "Activities" in response.text
