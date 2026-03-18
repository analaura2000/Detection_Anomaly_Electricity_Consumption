from flask import Flask, render_template, jsonify, request, send_from_directory
import joblib
import pandas as pd
import os

app = Flask(__name__)

# Load the XGBoost model using the absolute path
model_path = os.path.join(os.path.dirname(__file__), 'XGBoost.joblib')
model_xgb = joblib.load(model_path)

# Debug information about loaded model
print("Loaded model type:", type(model_xgb))
if hasattr(model_xgb, 'named_steps'):
    print("Pipeline steps:", model_xgb.named_steps.keys())
    if 'classifier' in model_xgb.named_steps:
        clf = model_xgb.named_steps['classifier']
        if hasattr(clf, 'feature_names_in_'):
            print("Classifier expects features:", clf.feature_names_in_)
if hasattr(model_xgb, 'feature_names_in_'):
    print("Model feature_names_in_:", model_xgb.feature_names_in_)

# Columns to drop initially
columns_to_drop_initial = [
]

# Columns to drop after mapping (removed features)
columns_to_drop_after = ['sector', 'tariff', 'volt_lvl', 'mov_type', 'prev_read', 'cons_ratio']

# Route to serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    
    if 'file' not in request.files:
        return jsonify({"error": "No file found in request"}), 400

    file = request.files['file']
    sheet_name = request.form.get('sheet_name')
    # If sheet_name is not provided (e.g., file has a single sheet),
    # use the first sheet (index 0) to avoid pandas returning a dict when using None.
    if not sheet_name:
        sheet_name = 0

    try:
        df = pd.read_excel(file, sheet_name=sheet_name)
    except ValueError:
        return jsonify({"error": "Sheet not found in the file"}), 404
    except Exception as e:
        return jsonify({"error": f"Error reading file: {str(e)}"}), 400
    
    if df is not None:
        # Use 'codcli' if it exists, otherwise use index
        if 'codcli' in df.columns:
            client_id = df['codcli'].astype(str)
        else:
            # Si no existe 'codcli', usar el índice como identificador
            client_id = df.index.astype(str)
        
        # Drop unnecessary columns, ignore errors if columns are missing
        df.drop(columns=columns_to_drop_initial, inplace=True, errors='ignore')
        
        # Rename columns using the mapping
        df.rename(columns=column_mapping, inplace=True)
        
        # Drop additional columns that were removed from the model
        df.drop(columns=columns_to_drop_after, inplace=True, errors='ignore')
    
        # 1. Handle NaN values in the last columns and compute ratio
        if 'consump' in df.columns and 'avg_cons' in df.columns:
            # Create the new column as the division of 'consump' by 'avg_cons'
            df.insert(df.columns.get_loc('avg_cons') + 1, 'cons_ratio', df['consump'] / (df['avg_cons'] + 1e-6))
            print("New column 'cons_ratio' added successfully.")
        else:
            print("Columns 'consump' or 'avg_cons' do not exist in the DataFrame.")
        
        # 2. Convertir columna codcli a numérico si existe (antes del relleno general)
        if 'codcli' in df.columns:
            df['codcli'] = pd.to_numeric(df['codcli'], errors='coerce').fillna(0)
            print("Converted 'codcli' to numeric")

        # 3. Rellenar NaNs en columnas numéricas con 0
        num_cols = df.select_dtypes(include=["number"]).columns
        if len(num_cols) > 0:
            df[num_cols] = df[num_cols].fillna(0)
            print(f"Filled NaNs with 0 in numeric columns: {list(num_cols)}")
        else:
            print("No numeric columns detected to fill NaNs.")
        # Not converting all columns to numeric: pipeline expects categorical strings
        
        # 3. Fill null values in other columns with mode or 'Other' where appropriate
        # Note: volt_lvl and mov_type are dropped, so no need to fill

        # Define columns where nulls should be replaced
        columns_to_fill = ['read_stat', 'insp_code']
        for col in columns_to_fill:
            if col in df.columns:
                df[col] = df[col].fillna('Other')

    # Debug: show dtypes before prediction
    print("Data types before prediction:\n", df.dtypes)

    # Restrict columns to those expected by the model (if available)
    expected_cols = None
    if hasattr(model_xgb, 'feature_names_in_'):
        expected_cols = list(model_xgb.feature_names_in_)
    elif hasattr(model_xgb, 'named_steps') and 'classifier' in model_xgb.named_steps:
        clf = model_xgb.named_steps['classifier']
        if hasattr(clf, 'feature_names_in_'):
            expected_cols = list(clf.feature_names_in_)
    if expected_cols is not None:
        missing = set(expected_cols) - set(df.columns)
        if missing:
            print(f"Warning: missing expected columns before prediction: {missing}")
        df = df.reindex(columns=expected_cols, fill_value=0)
        print(f"DataFrame trimmed to expected columns ({len(expected_cols)}).")

    # Make predictions
    try:
        predictions = model_xgb.predict(df)
    except Exception as e:
        return jsonify({"error": f"Error making prediction: {str(e)}"}), 500

    # Convert predictions to 'Yes' or 'No'
    results = []
    for i, pred in enumerate(predictions):
        # Acceder correctamente al client_id dependiendo de su tipo
        if isinstance(client_id, pd.Series):
            cid = str(client_id.iloc[i])
        else:
            cid = str(client_id[i])
        
        results.append({
            "client_id": cid,
            "anomaly": "Yes" if pred == 1 else "No"
        })
    
    print("Predictions generated:", results)
    return jsonify(results)

if __name__ == '__main__':

    app.run(debug=True, port=5000)  # Specify port to avoid conflicts