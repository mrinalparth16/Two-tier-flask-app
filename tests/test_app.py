import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app


class DevOpsTrackerTestCase(unittest.TestCase):
    """Test suite for DevOps Project Tracker web application."""

    def setUp(self):
        """Configure test client before each test."""
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def test_app_starts(self):
        """Verify the Flask application initializes properly."""
        self.assertIsNotNone(app)
        self.assertTrue(app.config["TESTING"])

    def test_health_check_endpoint(self):
        """Verify /health returns HTTP 200 or 503 with JSON payload."""
        response = self.client.get("/health")
        self.assertIn(response.status_code, [200, 503])
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertIn("status", data)
        self.assertIn("database", data)

    @patch("app.get_db_connection")
    def test_dashboard_route_success(self, mock_get_db):
        """Verify home/dashboard route loads successfully with project data."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock metric query
        mock_cursor.fetchone.return_value = {
            "total": 2,
            "planning": 1,
            "in_progress": 1,
            "completed": 0
        }
        # Mock project list
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "CI/CD Pipeline",
                "description": "Jenkins build and test setup",
                "technology": "Jenkins, Docker",
                "status": "In Progress",
                "created_at": None
            },
            {
                "id": 2,
                "name": "IaC AWS Setup",
                "description": "Terraform modules",
                "technology": "Terraform, AWS",
                "status": "Planning",
                "created_at": None
            }
        ]

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Project Overview", response.data)
        self.assertIn(b"CI/CD Pipeline", response.data)
        self.assertIn(b"IaC AWS Setup", response.data)

    @patch("app.get_db_connection")
    def test_dashboard_filter_by_status(self, mock_get_db):
        """Verify dashboard status filtering executes the expected query."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {"total": 1, "planning": 0, "in_progress": 1, "completed": 0}
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "Kubernetes Cluster",
                "description": "K8s setup",
                "technology": "Kubernetes",
                "status": "In Progress",
                "created_at": None
            }
        ]

        response = self.client.get("/?status=In+Progress")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Kubernetes Cluster", response.data)

    def test_add_project_page_get(self):
        """Verify the add project form page loads with HTTP 200."""
        response = self.client.get("/projects/add")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"New DevOps Project", response.data)
        self.assertIn(b"Project Name", response.data)
        self.assertIn(b"Technology / Stack", response.data)

    def test_add_project_validation_failure(self):
        """Verify form rejects submission when required fields are missing."""
        # Missing project name
        response = self.client.post(
            "/projects/add",
            data={
                "name": "",
                "technology": "Docker, Python",
                "status": "Planning",
                "description": "Some description"
            },
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Project name is required.", response.data)

        # Missing technology stack
        response = self.client.post(
            "/projects/add",
            data={
                "name": "My New Project",
                "technology": "",
                "status": "Planning",
                "description": "Some description"
            },
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Technology stack is required.", response.data)

    @patch("app.get_db_connection")
    def test_add_project_success(self, mock_get_db):
        """Verify successful project submission executes database insert and redirects."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        response = self.client.post(
            "/projects/add",
            data={
                "name": "Prometheus Monitoring",
                "technology": "Prometheus, Grafana",
                "status": "Planning",
                "description": "Metrics collection and alerting"
            }
        )
        # Should redirect to index upon creation
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        # Verify SQL insert was called
        self.assertTrue(mock_cursor.execute.called)

    @patch("app.get_db_connection")
    def test_view_project_found(self, mock_get_db):
        """Verify viewing an existing project displays all details."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            "id": 10,
            "name": "Terraform Infrastructure",
            "description": "Automated cloud provisioning",
            "technology": "Terraform, AWS",
            "status": "In Progress",
            "created_at": None
        }

        response = self.client.get("/projects/10")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Terraform Infrastructure", response.data)
        self.assertIn(b"Automated cloud provisioning", response.data)

    @patch("app.get_db_connection")
    def test_view_project_not_found(self, mock_get_db):
        """Verify viewing a non-existent project redirects gracefully."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = None

        response = self.client.get("/projects/9999")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")

    @patch("app.get_db_connection")
    def test_edit_project_post_success(self, mock_get_db):
        """Verify editing a project updates database and redirects to view page."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Initial fetch
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "name": "Old Name",
            "technology": "Docker",
            "status": "Planning",
            "description": "Old description",
            "created_at": None
        }

        response = self.client.post(
            "/projects/1/edit",
            data={
                "name": "Updated Pipeline Name",
                "technology": "Docker, Kubernetes",
                "status": "Completed",
                "description": "Updated description"
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/projects/1")
        self.assertTrue(mock_cursor.execute.called)

    @patch("app.get_db_connection")
    def test_delete_project_post_success(self, mock_get_db):
        """Verify deleting a project calls delete query and redirects."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {"name": "Test Project"}

        response = self.client.post("/projects/1/delete")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        self.assertTrue(mock_cursor.execute.called)


if __name__ == "__main__":
    unittest.main()
