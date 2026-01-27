import os
from flask import Flask, send_from_directory, render_template_string

app = Flask(__name__)

# Set the directory to serve files from (current directory of the script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Whitelist of files allowed for download
ALLOWED_FILES = [
    'final_hits_output.csv',
    'final_profile_output.csv'
]

@app.route('/')
def index():
    """
    Render the main page listing available result files.
    """
    # Check which files from the allowed list actually exist
    available_files = []
    for filename in ALLOWED_FILES:
        if os.path.exists(os.path.join(BASE_DIR, filename)):
            available_files.append(filename)
    
    # Simple HTML template for the download interface
    html = """
    <!doctype html>
    <html>
    <head>
        <title>Coursework Results</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 50px; background-color: #f4f4f9; }
            .container { background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            ul { list-style-type: none; padding: 0; }
            li { margin: 15px 0; background-color: #ecf0f1; padding: 10px; border-radius: 5px; }
            a { text-decoration: none; color: #2980b9; font-weight: bold; font-size: 18px; display: block; }
            a:hover { color: #3498db; }
            .footer { margin-top: 20px; font-size: 0.8em; color: #7f8c8d; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Analysis Download Center</h1>
            <p>Select a file below to download the analysis results:</p>
            {% if files %}
                <ul>
                    {% for file in files %}
                    <li>
                        <a href="/download/{{ file }}">⬇️ Download {{ file }}</a>
                    </li>
                    {% endfor %}
                </ul>
            {% else %}
                <p style="color: red; text-align: center;">No result files found yet. Please wait for the pipeline to finish.</p>
            {% endif %}
            <div class="footer">UCL EDA T1 Coursework - Result Server</div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, files=available_files)

@app.route('/download/<path:filename>')
def download_file(filename):
    """
    Serve the file if it is in the allowed list.
    """
    if filename in ALLOWED_FILES:
        return send_from_directory(BASE_DIR, filename, as_attachment=True)
    else:
        return "Access Denied: File not allowed.", 403

if __name__ == '__main__':
    # Run on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000)