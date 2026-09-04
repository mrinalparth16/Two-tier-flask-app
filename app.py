import os
import pymysql
import pymysql.cursors
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    jsonify
)

# Load environment variables from a .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devops-tracker-secret-key-change-in-production")

# Allowed project statuses
VALID_STATUSES = ["Planning", "In Progress", "Completed"]


def get_db_connection():
    """Establishes and returns a connection to the MySQL database."""
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "devops_tracker"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


@app.route("/")
def index():
    """Dashboard view: Displays metric summary cards and the project list with optional filtering."""
    status_filter = request.args.get("status", "").strip()

    projects = []
    stats = {
        "total": 0,
        "planning": 0,
        "in_progress": 0,
        "completed": 0
    }
    db_error = None

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Query status counts for dashboard metric cards
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'Planning' THEN 1 ELSE 0 END) AS planning,
                    SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed
                FROM projects
                """
            )
            count_result = cursor.fetchone()
            if count_result:
                stats["total"] = count_result["total"] or 0
                stats["planning"] = int(count_result["planning"] or 0)
                stats["in_progress"] = int(count_result["in_progress"] or 0)
                stats["completed"] = int(count_result["completed"] or 0)

            # Query projects list with optional status filter
            if status_filter in VALID_STATUSES:
                query = "SELECT * FROM projects WHERE status = %s ORDER BY created_at DESC, id DESC"
                cursor.execute(query, (status_filter,))
            else:
                status_filter = "All"
                query = "SELECT * FROM projects ORDER BY created_at DESC, id DESC"
                cursor.execute(query)

            projects = cursor.fetchall()
        connection.close()

    except Exception as exc:
        db_error = f"Database connection error: {str(exc)}"

    return render_template(
        "index.html",
        projects=projects,
        stats=stats,
        current_filter=status_filter,
        status_options=VALID_STATUSES,
        db_error=db_error
    )


@app.route("/projects/add", methods=["GET", "POST"])
def add_project():
    """Renders the project creation form (GET) and processes new project submissions (POST)."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        technology = request.form.get("technology", "").strip()
        status = request.form.get("status", "Planning").strip()
        description = request.form.get("description", "").strip()

        # Validation
        errors = []
        if not name:
            errors.append("Project name is required.")
        elif len(name) > 150:
            errors.append("Project name must not exceed 150 characters.")

        if not technology:
            errors.append("Technology stack is required.")
        elif len(technology) > 255:
            errors.append("Technology stack must not exceed 255 characters.")

        if status not in VALID_STATUSES:
            errors.append("Invalid status selected.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template(
                "add_project.html",
                name=name,
                technology=technology,
                status=status,
                description=description,
                status_options=VALID_STATUSES
            ), 400

        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO projects (name, description, technology, status)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (name, description, technology, status))
            connection.close()

            flash(f"Project '{name}' was successfully created!", "success")
            return redirect(url_for("index"))

        except Exception as exc:
            flash(f"Failed to save project to database: {str(exc)}", "danger")
            return render_template(
                "add_project.html",
                name=name,
                technology=technology,
                status=status,
                description=description,
                status_options=VALID_STATUSES
            ), 500

    return render_template("add_project.html", status_options=VALID_STATUSES)


@app.route("/projects/<int:project_id>")
def view_project(project_id):
    """Displays detailed information for a specific project."""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            project = cursor.fetchone()
        connection.close()

        if not project:
            flash("The requested project could not be found.", "warning")
            return redirect(url_for("index"))

        return render_template("project.html", project=project)

    except Exception as exc:
        flash(f"Database error while fetching project details: {str(exc)}", "danger")
        return redirect(url_for("index"))


@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
def edit_project(project_id):
    """Renders the edit form (GET) and updates project information (POST)."""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            project = cursor.fetchone()
        connection.close()

        if not project:
            flash("The requested project does not exist.", "warning")
            return redirect(url_for("index"))

    except Exception as exc:
        flash(f"Database error: {str(exc)}", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        technology = request.form.get("technology", "").strip()
        status = request.form.get("status", "Planning").strip()
        description = request.form.get("description", "").strip()

        errors = []
        if not name:
            errors.append("Project name is required.")
        elif len(name) > 150:
            errors.append("Project name must not exceed 150 characters.")

        if not technology:
            errors.append("Technology stack is required.")
        elif len(technology) > 255:
            errors.append("Technology stack must not exceed 255 characters.")

        if status not in VALID_STATUSES:
            errors.append("Invalid status selected.")

        if errors:
            for error in errors:
                flash(error, "danger")
            project_data = {
                "id": project_id,
                "name": name,
                "technology": technology,
                "status": status,
                "description": description,
                "created_at": project.get("created_at")
            }
            return render_template(
                "edit_project.html",
                project=project_data,
                status_options=VALID_STATUSES
            ), 400

        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                sql = """
                    UPDATE projects
                    SET name = %s, description = %s, technology = %s, status = %s
                    WHERE id = %s
                """
                cursor.execute(sql, (name, description, technology, status, project_id))
            connection.close()

            flash(f"Project '{name}' was updated successfully!", "success")
            return redirect(url_for("view_project", project_id=project_id))

        except Exception as exc:
            flash(f"Failed to update project: {str(exc)}", "danger")
            return render_template(
                "edit_project.html",
                project=project,
                status_options=VALID_STATUSES
            ), 500

    return render_template("edit_project.html", project=project, status_options=VALID_STATUSES)


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
def delete_project(project_id):
    """Deletes a project record from the database after confirmation."""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Confirm project exists first
            cursor.execute("SELECT name FROM projects WHERE id = %s", (project_id,))
            project = cursor.fetchone()
            if not project:
                flash("Project not found.", "warning")
                connection.close()
                return redirect(url_for("index"))

            cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
        connection.close()

        flash(f"Project '{project['name']}' was successfully deleted.", "success")
    except Exception as exc:
        flash(f"Failed to delete project: {str(exc)}", "danger")

    return redirect(url_for("index"))


@app.route("/health")
def health():
    """Health check endpoint for container probes and monitoring."""
    db_status = "disconnected"
    status_code = 200
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        connection.close()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
        status_code = 503

    return jsonify({
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status
    }), status_code


@app.errorhandler(404)
def not_found_error(error):
    """404 Not Found error handler."""
    return render_template("base.html", error_title="404 - Page Not Found", error_message="The requested resource could not be found."), 404


@app.errorhandler(500)
def internal_error(error):
    """500 Internal Server Error handler."""
    return render_template("base.html", error_title="500 - Server Error", error_message="An unexpected internal server error occurred."), 500


if __name__ == "__main__":
    # In local development, run with debug mode enabled
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
