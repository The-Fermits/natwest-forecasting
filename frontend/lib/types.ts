// TypeScript interfaces for the NatWest Forecasting Dashboard

export interface HistoricalPoint {
  date: string;
  value: number;
}

export interface ForecastPoint {
  date: string;
  lower: number;
  central: number;
  upper: number;
}

export interface BaselinePoint {
  date: string;
  value: number;
}

export interface AnomalyPoint {
  date: string;
  value: number;
  zscore: number;
  iqr_outlier: boolean;
  is_anomaly: boolean;
  severity: 'warning' | 'critical';
  expected_range: [number, number];
  explanation?: string;
  warning_type?: string;
  historical_band?: [number, number];
}

export interface ModelAccuracy {
  mape: number | null;
  rmse: number | null;
  baseline_naive_mape: number;
  baseline_naive_rmse: number;
  baseline_ma_mape: number;
  baseline_ma_rmse: number;
  outperformance_pct: number;
}

export interface Patterns {
  trend: 'upward' | 'downward' | 'flat';
  seasonality_period: number | null;
  seasonality_strength: number | null;
}

export interface DataQualityCheck {
  check: string;
  status: 'pass' | 'warn' | 'fail';
  detail: string;
}

export interface TrainingRange {
  start: string;
  end: string;
  period_count: number;
}

export interface ForecastResponse {
  historical: HistoricalPoint[];
  forecast: ForecastPoint[];
  baseline_naive: BaselinePoint[];
  baseline_ma: BaselinePoint[];
  model_used: 'Prophet' | 'AutoETS';
  accuracy: ModelAccuracy;
  patterns: Patterns;
  anomalies: AnomalyPoint[];
  data_quality: DataQualityCheck[];
  metric_label: string;
  training_range: TrainingRange;
  confidence_level: number;
}

export interface UploadResponse {
  session_id: string;
  preview: Record<string, string | number>[];
  detected_date_col: string;
  detected_value_col: string;
  period_count: number;
  frequency: string;
}

export interface ScenarioResponse {
  scenario_forecast: ForecastPoint[];
  diff_summary: string;
}

export type MetricKey =
  | 'transaction_volume'
  | 'loan_disbursements'
  | 'default_rates'
  | 'new_signups'
  | 'churn_rate'
  | 'support_tickets';

export const METRIC_LABELS: Record<MetricKey, string> = {
  transaction_volume: 'Transaction Volume',
  loan_disbursements: 'Loan Disbursements',
  default_rates: 'Default Rates (%)',
  new_signups: 'New Customer Signups',
  churn_rate: 'Customer Churn Rate (%)',
  support_tickets: 'Support Tickets',
};

export type DataMode = 'default' | 'upload';
export type ConfidenceLevel = 0.80 | 0.95;
