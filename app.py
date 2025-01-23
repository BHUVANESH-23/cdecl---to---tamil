import os
import subprocess
from functools import lru_cache
from flask import Flask, request, render_template, jsonify
import requests
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    filename="app.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

SYNTAX_ERROR = "syntax error"
current_directory = os.getcwd()
executable_path = os.path.join(current_directory, "c++decl.exe")

# Check if the executable exists
if not os.path.isfile(executable_path):
    raise FileNotFoundError(f"Executable not found: {executable_path}")

command = [executable_path]


def to_Tamil(text: str) -> str:
    """Convert text to Tamil using Google's transliteration API."""
    try:
        url = "https://inputtools.google.com/request"
        data = {
            "itc": "ta-t-i0-und",  # Tamil transliteration code
            "num": 1,
            "cp": 0,
            "text": text,
        }
        response = requests.post(url, data=data)
        response_data = response.json()

        if response_data[0] == "SUCCESS":
            transliterations = response_data[1][0][1]
            return " ".join(transliterations)
        else:
            app.logger.error(f"Error in transliteration: {response_data}")
            return "Error in transliteration."
    except Exception as e:
        app.logger.error(f"Transliteration error: {e}")
        return "Transliteration error."


@lru_cache(None)
def translate(query: str) -> str:
    """Translate C declarations into Tamil."""
    try:
        app.logger.info(f"Cache Info: {translate.cache_info()}")
        storage_classes = ["auto", "extern", "static", "register"]
        q_l = query.split()

        # Handle syntax error cases
        if q_l[0] in ("declare", "cast"):
            return to_Tamil(SYNTAX_ERROR)

        # Fix incomplete declarations
        if len(q_l) < 3 and q_l[0] in storage_classes:
            query = f"{q_l[0]} int {q_l[1]}"

        queries = [query, f"explain {query};", f"declare {query};"]

        # Execute the subprocess
        with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            output, error = process.communicate(input="\n".join(queries).encode())

            if process.returncode != 0:
                app.logger.error(f"Subprocess error: {error.decode()}")
                return to_Tamil("Subprocess execution error.")

            for line in output.splitlines():
                line = line.decode()
                if line and line != SYNTAX_ERROR:
                    app.logger.info(f"Subprocess output: {line}")
                    return to_Tamil(line)

        return to_Tamil(SYNTAX_ERROR)
    except FileNotFoundError as e:
        app.logger.error(f"Executable not found: {e}")
        return to_Tamil("Executable not found.")
    except Exception as e:
        app.logger.error(f"Error during translation: {e}")
        return to_Tamil("Error during translation.")


def handle_help_request() -> str:
    """Handle 'help' requests."""
    return to_Tamil("சின்டாக்ஸ் பிழை")  # Syntax error in Tamil


@app.route("/", methods=["GET", "POST"])
def index():
    """Handle the main route."""
    if request.method == "POST":
        try:
            query = request.form.get("query", "").strip()  # Extract query from form data
            if query:
                if query.lower() == "help":
                    return jsonify({"output": handle_help_request()})
                return jsonify({"output": translate(query)})
            return jsonify({"error": to_Tamil("Invalid input provided.")}), 400
        except Exception as e:
            app.logger.error(f"Unhandled exception: {e}")
            return jsonify({"error": "Internal server error occurred."}), 500
    return render_template("index.html")


@app.after_request
def add_content_type(response):
    """Ensure the Content-Type is application/json for JSON responses."""
    if response.mimetype == "application/json":
        response.headers["Content-Type"] = "application/json"
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
