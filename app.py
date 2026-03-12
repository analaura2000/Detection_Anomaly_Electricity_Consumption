"""
Simple Flask application for running predictions with a pre-trained model.
Accepts an Excel file upload and returns predictions.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
import joblib
import pandas as pd
import os

# instantiate the Flask application
app = Flask(__name__)

# Load the serialized XGBoost model file. Using os.path helps ensure the
# correct absolute path regardless of the working directory when the
# server is started. The model is expected to be in the same folder as
# this script.
modelo_path = os.path.join(os.path.dirname(__file__), 'XGBoost.joblib')
modelo_xgb = joblib.load(modelo_path)

# Route to serve files from the static directory. This allows CSS,
# JavaScript, images, etc. to be requested by the browser.
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


# Root endpoint renders the main HTML page containing the file upload
# interface and result table.
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint to receive an Excel file and return predictions.

    Expected form data:
    - archivo: uploaded file object
    - sheet_name (optional): name or index of sheet to read
    """

    # validate incoming file
    if 'archivo' not in request.files:
        return jsonify({"error": "File not found in request"}), 400

    file = request.files['archivo']

    # read sheet identifier from form; may be None
    sheet_name = request.form.get('sheet_name')
    # if not provided, default to first sheet
    if not sheet_name:
        sheet_name = 0

    # attempt to load the Excel data into a DataFrame
    try:
        df = pd.read_excel(file, sheet_name=sheet_name)
    except ValueError:
        return jsonify({"error": "Sheet not found in file"}), 404
    except Exception as e:
        return jsonify({"error": f"Error reading file: {str(e)}"}), 400

    if df.empty or df.shape[1] < 2:
        return jsonify({"error": "Data must have at least 2 columns: ID and features"}), 400

    # Assume first column is ID
    id_col = df.iloc[:, 0]
    features = df.iloc[:, 1:]

    # Make predictions
    try:
        predictions = modelo_xgb.predict(features)
    except Exception as e:
        return jsonify({"error": f"Error making prediction: {str(e)}"}), 500

    # Format output
    results = []
    for i, pred in enumerate(predictions):
        results.append({
            "id": str(id_col.iloc[i]),
            "prediction": int(pred)
        })

    return jsonify(results)

if __name__ == '__main__':

    app.run(debug=True, port=5000)  # specify port to avoid conflicts