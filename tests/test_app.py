import pytest
from fastapi.testclient import TestClient
from src.app import app

# Create a test client
client = TestClient(app)

def test_root_redirect():
    """Test that root URL returns static/index.html"""
    response = client.get("/")
    assert response.status_code == 200  # OK status code for RedirectResponse

def test_get_activities():
    """Test getting the list of activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    # Check that we get a dictionary of activities
    assert isinstance(activities, dict)
    
    # Check that each activity has the required fields
    for activity_name, details in activities.items():
        assert isinstance(activity_name, str)
        assert isinstance(details, dict)
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)

def test_signup_for_activity():
    """Test signing up for an activity"""
    activity_name = "Chess Club"
    email = "test@mergington.edu"
    
    # Try signing up
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    # Verify the participant was added
    activities = client.get("/activities").json()
    assert email in activities[activity_name]["participants"]
    
    # Try signing up again (should fail)
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]

def test_unregister_from_activity():
    """Test unregistering from an activity"""
    activity_name = "Chess Club"
    email = "test@mergington.edu"
    
    # First, make sure the participant is signed up
    if email not in client.get("/activities").json()[activity_name]["participants"]:
        client.post(f"/activities/{activity_name}/signup?email={email}")
    
    # Try unregistering
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    
    # Verify the participant was removed
    activities = client.get("/activities").json()
    assert email not in activities[activity_name]["participants"]
    
    # Try unregistering again (should fail)
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 404
    assert "not found in this activity" in response.json()["detail"]

def test_signup_nonexistent_activity():
    """Test signing up for a non-existent activity"""
    response = client.post("/activities/NonexistentClub/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_unregister_nonexistent_activity():
    """Test unregistering from a non-existent activity"""
    response = client.delete("/activities/NonexistentClub/unregister?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_max_participants():
    """Test that activities enforce maximum participant limits"""
    activity_name = "Chess Club"
    activities = client.get("/activities").json()
    max_participants = activities[activity_name]["max_participants"]
    current_participants = len(activities[activity_name]["participants"])
    
    # Add participants until we reach the maximum
    for i in range(current_participants, max_participants):
        email = f"test{i}@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
    
    # Try to add one more participant
    response = client.post(f"/activities/{activity_name}/signup?email=extra@mergington.edu")
    assert response.status_code == 400
    assert "at maximum capacity" in response.json()["detail"]