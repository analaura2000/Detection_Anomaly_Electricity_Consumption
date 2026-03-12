# Detection_Anomaly_Electricity_Consumption

This project implements a complete machine learning pipeline based on XGBoost, including data analysis, model training in a Jupyter notebook, a REST API backend, and a web interface for generating predictions.

## Repository structure

```
FINAL.ipynb         # Data analysis, preprocessing, model training, evaluation
app.py              # REST API backend for predictions
templates/
    index.html      # Web interface for predictions
static/
    scripts.js
    styles.css
    logo.png
```

## Requirements

- Python 3.7 or higher
- Packages:
  - flask
  - pandas
  - joblib
  - scikit-learn (needed only if you retrain the model)

## Getting Started

### Step 1: Train the Model

1. Open `FINAL.ipynb` in Jupyter:
   ```bash
   jupyter notebook FINAL.ipynb
   ```

2. Follow the notebook to:
   - Load and explore your data
   - Perform preprocessing and feature engineering
   - Train the methods
   - Evaluate performance
   - Save the model as `XGBoost.joblib`

### Step 2: Deploy and Use the Prediction Web Interface

Once you have `XGBoost.joblib`, deploy the prediction API:

1. Install requirements:
   ```bash
   pip install flask pandas joblib scikit-learn
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. Open your browser at `http://localhost:5000`

4. Use the web interface to:
   - Upload an `.xlsx` file with at least 2 columns (ID + features)
   - Select the sheet if the file has multiple sheets
   - Click **Predict** to get results
   - Download results as Excel

## Architecture

**1. Model Training (`FINAL.ipynb`)**
- Data exploration and preprocessing
- Feature engineering
- Training multiple machine learning methods
- Performance evaluation
- Model export as `XGBoost.joblib`

**2. Prediction API (`app.py`)**
- Flask REST API backend
- Loads pre-trained XGBoost method
- Accepts Excel files with data
- Returns predictions as JSON

**3. Web Interface (`templates/index.html`)**
- User-friendly file upload interface
- Sheet selection for multi-sheet Excel files
- Results table with pagination
- Excel export functionality

## Important Notes

- The prediction phase expects data in the same format as the training data (no preprocessing applied during API calls)
- First column is treated as ID, remaining columns are features
- Ensure your input Excel file matches the feature structure used during method training




