import subprocess
import os
from functools import lru_cache
from flask import Flask, request, render_template, jsonify
import requests

app = Flask(__name__)


SYNTAX_ERROR = "syntax error"
current_directory = os.getcwd()
command = [os.path.join(current_directory, "./c++decl.exe")]  


def to_Tamil(text: str) -> str:
    try:
        url = "https://inputtools.google.com/request"
        data = {
            "itc": "ta-t-i0-und",  
            "num": 1,
            "cp": 0,
            "text": text
        }
        response = requests.post(url, data=data)
        response_data = response.json()
        
        if response_data[0] == "SUCCESS":
            transliterations = response_data[1][0][1]
            return " ".join(transliterations)
        else:
            return f"Error in transliteration: {response_data}"
    except Exception as e:
        return f"Transliteration error: {e}"


@lru_cache(None)
def translate(query: str) -> str:
    print(f"translate : {translate.cache_info()}")
    storage_classes = ["auto", "extern", "static", "register"]
    q_l = query.split()

    
    if q_l[0] in ("declare", "cast"):
        return to_Tamil(SYNTAX_ERROR)  

    
    if len(q_l) < 3 and q_l[0] in storage_classes:
        query = f"{q_l[0]} int {q_l[1]}"

    
    queries = [query, f"explain {query};", f"declare {query};"]

    
    translated_text = None
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as process:
        output, _ = process.communicate(input="\n".join(queries).encode())
        for line in output.splitlines():
            line = line.decode()
            if line and line != SYNTAX_ERROR:
                print(line)  
                translated_text = to_Tamil(line)  
                break

    return translated_text or to_Tamil(SYNTAX_ERROR)  


def handle_help_request() -> str:

    return to_Tamil("சின்டாக்ஸ் பிழை")  

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form.get("query", "")
        if query:
            if query.lower() == "help":
                return jsonify({"output": handle_help_request()})  
            return jsonify({"output": translate(query.strip())})  
        return jsonify({"error": to_Tamil("பிழை")})  
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
