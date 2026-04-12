# API Reference

Base URL: `http://localhost:8000` (dev) | `https://<your-render-url>` (prod)

---

## GET /health
Returns service health.

**Response:**
```json
{ "status": "ok", "model_ready": true }
```

---

## POST /upload
Upload a CSV file for forecasting.

**Request:** `multipart/form-data` with field `file` (CSV).

**Response:**
```json
{
  "session_id": "uuid-string",
  "preview": [{"date": "2023-01-02", "value": 12050.0}, ...],
  "detected_date_col": "date",
  "detected_value_col": "value",
  "period_count": 78,
  "frequency": "W"
}
```

**Errors:** 400 if not CSV, file too large, or columns cannot be detected.

---

## POST /forecast
Run the full forecasting pipeline.

**Request:**
```json
{
  "metric": "transaction_volume",
  "session_id": null,
  "horizon_weeks": 4,
  "confidence_level": 0.80
}
```

`metric` values: `transaction_volume | loan_disbursements | default_rates | new_signups | churn_rate | support_tickets`

**Response:**
```json
{
  "historical": [{"date": "2023-01-02", "value": 12050.0}],
  "forecast": [{"date": "2024-10-07", "lower": 11800.0, "central": 13200.0, "upper": 14600.0}],
  "baseline_naive": [{"date": "...", "value": 12400.0}],
  "baseline_ma": [{"date": "...", "value": 12100.0}],
  "model_used": "Prophet",
  "accuracy": {
    "mape": 4.2, "rmse": 540.0,
    "baseline_naive_mape": 7.1, "baseline_naive_rmse": 890.0,
    "baseline_ma_mape": 6.2, "baseline_ma_rmse": 750.0,
    "outperformance_pct": 32.4
  },
  "patterns": {"trend": "upward", "seasonality_period": 52, "seasonality_strength": 0.62},
  "anomalies": [{"date": "2024-03-18", "value": 18900.0, "zscore": 2.8, "severity": "warning", "expected_range": [10200, 14800]}],
  "data_quality": [{"check": "missing_values", "status": "pass", "detail": "0 missing values"}],
  "metric_label": "Transaction Volume",
  "training_range": {"start": "2023-01-02", "end": "2024-10-01", "period_count": 104},
  "confidence_level": 0.80
}
```

---

## POST /anomaly
Run anomaly detection only.

**Request:** `{ "metric": "transaction_volume", "session_id": null }`

**Response:** `{ "anomalies": [...], "total": 3 }`

---

## POST /scenario
Apply what-if adjustments to a base forecast.

**Request:**
```json
{
  "base_forecast": [...],
  "growth_rate": 0.10,
  "remove_outliers": false,
  "seasonal_boost": {"week": 3, "pct": 0.05}
}
```

**Response:**
```json
{
  "scenario_forecast": [...],
  "diff_summary": "Under +10% growth, Week 4 reaches 14,520 vs 13,200 baseline. Range: 13,800–15,300."
}
```

---

## GET /briefing (SSE)
Stream a Claude AI plain-English briefing.

**Query params:** `metric`, `trend`, `horizon`, `anomaly_count`, `forecast_summary`, `model_used`

**Response:** `text/event-stream`
```
data: {"token": "Transaction"}
data: {"token": " volumes"}
...
data: {"done": true}
```
