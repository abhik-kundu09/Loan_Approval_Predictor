# 🏦 Loan Approval Predictor

An end-to-end machine learning web application that predicts whether a bank loan application will be **Approved** or **Rejected** — built with FastAPI, Streamlit, and Scikit-learn.

---

## 🖥️ Live Demo

> _Deploy link will appear here after deployment_

---

## 📸 Preview

> _Add a screenshot of the app here_

---

## ✨ Features

- **Instant predictions** — real-time loan approval decision via a trained ML model
- **Confidence scores** — approval/rejection probabilities with a visual risk gauge
- **DTI analysis** — automatic debt-to-income ratio check against the 43% underwriting threshold
- **Prediction history** — session-based log of the last 5 predictions
- **Input validation** — client-side checks before hitting the API
- **REST API** — standalone FastAPI backend with `/predict`, `/health`, and `/model-info` endpoints

---

## 🗂️ Project Structure

```
loan-predictor/
├── app.py                  # Streamlit frontend
├── requirements.txt
├── PLAN.md
├── api/
│   ├── __init__.py
│   ├── main.py             # FastAPI app & prediction logic
│   └── schemas.py          # Pydantic request/response models
├── models/
│   ├── best_model.pkl      # Trained Decision Tree model
│   └── scaler.pkl          # Fitted StandardScaler
├── data/                   # Raw & processed dataset
└── notebooks/
    └── loan_predictor.ipynb  # EDA, training, evaluation
```

---

## 🤖 ML Pipeline

| Step | Detail |
|------|--------|
| Dataset | Loan Prediction Dataset — 614 records, 11 features |
| Task | Binary classification (Approved / Rejected) |
| Models trained | Logistic Regression, Decision Tree, Random Forest |
| Selected model | **Decision Tree Classifier** (best F1-score) |
| Preprocessing | Label encoding + StandardScaler on numeric features |

**Key insight:** Credit history is the strongest single predictor of loan approval.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Streamlit, Plotly |
| Backend | FastAPI, Uvicorn |
| ML | Scikit-learn, Pandas, NumPy |
| Serialization | Joblib |

---

## 🚀 Running Locally

### 1. Clone & install

```bash
git clone https://github.com/your-username/loan-predictor.git
cd loan-predictor
pip install -r requirements.txt
```

### 2. Start the API

```bash
uvicorn api.main:app --reload
# Running at http://localhost:8000
```

### 3. Start the Streamlit app

```bash
streamlit run app.py
# Running at http://localhost:8501
```

### API docs (auto-generated)

```
http://localhost:8000/docs
```

---

## 📡 API Reference

### `POST /predict`

**Request body:**
```json
{
  "Gender": "Male",
  "Married": "Yes",
  "Dependents": "0",
  "Education": "Graduate",
  "Self_Employed": "No",
  "ApplicantIncome": 5000,
  "CoapplicantIncome": 0,
  "LoanAmount": 150,
  "Loan_Amount_Term": 360,
  "Credit_History": 1,
  "Property_Area": "Urban"
}
```

**Response:**
```json
{
  "prediction": "Approved",
  "confidence": 0.92,
  "approve_probability": 0.92,
  "reject_probability": 0.08,
  "model_used": "DecisionTreeClassifier"
}
```

### Other endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Model status |
| GET | `/model-info` | Feature list & model name |

---

## 📦 Requirements

```
streamlit
fastapi
uvicorn
scikit-learn
pandas
numpy
joblib
plotly
requests
pydantic
```

---

## 👤 Author

**Abhik Kundu**  
Built with FastAPI · Streamlit · Scikit-Learn · Plotly