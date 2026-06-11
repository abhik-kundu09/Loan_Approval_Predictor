from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd

from api.schemas import LoanInput, PredictionResponse

app = FastAPI(
    title="Loan Approval Predictor API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Load Model & Scaler
# =========================

MODEL_PATH  = "models/best_model.pkl"
SCALER_PATH = "models/scaler.pkl"

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    MODEL_NAME = model.__class__.__name__

    print(f"Model loaded: {MODEL_NAME}")

except FileNotFoundError:
    raise RuntimeError(
        "best_model.pkl or scaler.pkl not found."
    )


# =========================
# Preprocessing
# =========================

def preprocess_input(data: LoanInput):

    gender_map = {
        "Female": 0,
        "Male": 1
    }

    married_map = {
        "No": 0,
        "Yes": 1
    }

    dependents_map = {
        "0": 0,
        "1": 1,
        "2": 2,
        "3+": 3
    }

    education_map = {
        "Graduate": 0,
        "Not Graduate": 1
    }

    self_emp_map = {
        "No": 0,
        "Yes": 1
    }

    property_map = {
        "Rural": 0,
        "Semiurban": 1,
        "Urban": 2
    }

    row = {
        "Gender": gender_map[data.Gender],
        "Married": married_map[data.Married],
        "Dependents": dependents_map[data.Dependents],
        "Education": education_map[data.Education],
        "Self_Employed": self_emp_map[data.Self_Employed],
        "ApplicantIncome": data.ApplicantIncome,
        "CoapplicantIncome": data.CoapplicantIncome,
        "LoanAmount": data.LoanAmount,
        "Loan_Amount_Term": data.Loan_Amount_Term,
        "Credit_History": data.Credit_History,
        "Property_Area": property_map[data.Property_Area]
    }

    df = pd.DataFrame([row])

    cols_to_scale = [
        "ApplicantIncome",
        "CoapplicantIncome",
        "LoanAmount",
        "Loan_Amount_Term"
    ]

    df[cols_to_scale] = scaler.transform(
        df[cols_to_scale]
    )

    return df


# =========================
# Routes
# =========================

@app.get("/")
def root():
    return {
        "message": "Loan Approval Predictor API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL_NAME
    }


@app.get("/model-info")
def model_info():

    return {
        "model_name": MODEL_NAME,
        "features": [
            "Gender",
            "Married",
            "Dependents",
            "Education",
            "Self_Employed",
            "ApplicantIncome",
            "CoapplicantIncome",
            "LoanAmount",
            "Loan_Amount_Term",
            "Credit_History",
            "Property_Area"
        ]
    }


@app.post(
    "/predict",
    response_model=PredictionResponse
)
def predict(data: LoanInput):

    try:

        df_input = preprocess_input(data)

        prediction = model.predict(df_input)[0]

        probabilities = model.predict_proba(df_input)[0]

        return PredictionResponse(
            prediction="Approved" if prediction == 1 else "Rejected",
            confidence=round(float(max(probabilities)), 4),
            approve_probability=round(float(probabilities[1]), 4),
            reject_probability=round(float(probabilities[0]), 4),
            model_used=MODEL_NAME
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )