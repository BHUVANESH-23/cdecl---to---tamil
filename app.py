import subprocess
import os
from functools import lru_cache
from flask import Flask, request, render_template, jsonify
import requests

app = Flask(__name__)

# Constants
SYNTAX_ERROR = "syntax error"
current_directory = os.getcwd()
executable_path = os.path.join(current_directory, "c++decl.exe")

# Validate if the executable exists
if not os.path.isfile(executable_path):
    raise FileNotFoundError(f"Executable not found: {executable_path}")

command = [executable_path]


def to_Tamil(text: str) -> str:
    """Transliterates the given text to Tamil using Google's Input Tools API."""
    try:
        url = "https://inputtools.google.com/request"
        data = {
            "itc": "ta-t-i0-und",
            "num": 1,
            "cp": 0,
            "text": text,
        }
        response = requests.post(url, data=data)
        response.raise_for_status()  # Raises HTTPError for bad responses
        response_data = response.json()
        
        if response_data[0] == "SUCCESS":
            transliterations = response_data[1][0][1]
            return " ".join(transliterations)
        else:
            return f"Error in transliteration: {response_data}"
    except requests.exceptions.RequestException as e:
        return f"Transliteration API error: {e}"
    except Exception as e:
        return f"Transliteration error: {e}"


@lru_cache(None)
def translate(query: str) -> str:
    """Translates a query using the c++decl executable and returns the Tamil transliteration."""
    try:
        print(f"translate: {translate.cache_info()}")
        storage_classes = ["auto", "extern", "static", "register"]
        q_l = query.split()

        # Handle syntax error scenarios
        if q_l[0] in ("declare", "cast"):
            return to_Tamil(SYNTAX_ERROR)

        # Handle single word queries like 'static' or 'extern'
        if len(q_l) < 3 and q_l[0] in storage_classes:
            query = f"{q_l[0]} int {q_l[1]}"

        # Form queries for the subprocess
        queries = [query, f"explain {query};", f"declare {query};"]

        # Run the subprocess and capture output
        with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            output, error = process.communicate(input="\n".join(queries).encode())
            if process.returncode != 0:
                error_message = error.decode().strip()
                return to_Tamil(f"Subprocess error: {error_message}")

            for line in output.splitlines():
                line = line.decode()
                if line and line != SYNTAX_ERROR:
                    print(line)
                    return to_Tamil(line)

        # Return syntax error if no valid output was found
        return to_Tamil(SYNTAX_ERROR)
    except FileNotFoundError:
        return to_Tamil("Executable not found.")
    except Exception as e:
        return to_Tamil(f"Error during translation: {e}")


def handle_help_request() -> str:
    """Handles 'help' requests and returns a Tamil message."""
    return to_Tamil("சின்டாக்ஸ் பிழை")


@app.route("/", methods=["GET", "POST"])
def index():
    """Handles the main route for the application."""
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            if query.lower() == "help":
                return jsonify({"output": handle_help_request()})
            try:
                return jsonify({"output": translate(query)})
            except Exception as e:
                # Catch any unhandled exception and log it
                return jsonify({"error": f"Unhandled server error: {e}"}), 500
        return jsonify({"error": to_Tamil("Invalid input provided.")}), 400
    return render_template("index.html")


# Entry point for the Flask application
if __name__ == "__main__":
    try:
        app.run(host="127.0.0.1", port=5000)
    except Exception as e:
        print(f"Failed to start the Flask application: {e}")
