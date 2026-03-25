// ─── Shared / utility ─────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: string,
  ) {
    super(`API ${status}: ${body}`)
    this.name = 'ApiError'
  }
}

// ─── /health ──────────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  cache_warm: boolean
  warmup_errors: Record<string, string> | null
  data_version: number
}

// ─── /warmup-status ───────────────────────────────────────────────

export interface WarmupStatusResponse {
  running: boolean
  done: boolean
  results: Record<string, string>
  errors: Record<string, string>
}

// ─── /fitness ─────────────────────────────────────────────────────

export interface FitnessData {
  CTL: number
  ATL: number
  TSB: number
  date: string
}

// ─── /pmc ─────────────────────────────────────────────────────────

export interface PMCRow {
  date: string
  TSS: number
  CTL: number
  ATL: number
  TSB: number
}

// ─── /clinical-flags ──────────────────────────────────────────────

export interface ClinicalFlag {
  name: string
  status: 'ok' | 'warning' | 'danger'
  value: string | number
  threshold: string
  detail: string
}

export interface ClinicalFlagsResponse {
  flags: ClinicalFlag[]
  alert_level: string
  error?: string
}

// ─── /profile ─────────────────────────────────────────────────────

export interface PowerProfileValues {
  watts: Record<string, number>
  wkg: Record<string, number>
}

export interface CogganRanking {
  [duration: string]: string
}

export interface StrengthLimiterEntry {
  duration: number
  label: string
  category: string
}

export interface StrengthsLimiters {
  strength: StrengthLimiterEntry
  limiter: StrengthLimiterEntry
}

export interface ProfileResponse {
  profile: PowerProfileValues
  ranking: CogganRanking
  strengths_limiters: StrengthsLimiters
  error?: string
}

// ─── /config ──────────────────────────────────────────────────────

export interface AthleteConfig {
  id: number
  name: string
  sex: string
  weight_kg: number
  max_hr: number
  lthr: number | null
  ftp_manual: number
  bike_weight_kg: number
  cda: number
  crr: number
  pd_pmax_low: number
  pd_pmax_high: number
  pd_mftp_low: number
  pd_mftp_high: number
  pd_frc_low: number
  pd_frc_high: number
  pd_tau_low: number
  pd_tau_high: number
  pd_t0_low: number
  pd_t0_high: number
  spike_threshold_watts: number
  resting_hr_baseline: number | null
  hrv_baseline: number | null
  resting_hr_alert_delta: number
  ctl_ramp_rate_yellow: number
  ctl_ramp_rate_red: number
  tsb_floor_alert: number
  collapse_kj_threshold: number | null
  intensity_ceiling_if: number
  fueling_rate_g_hr: number
  energy_deficit_alert_kcal: number
  ctl_time_constant: number
  atl_time_constant: number
}

// ─── /model ───────────────────────────────────────────────────────

export interface ModelResult {
  Pmax: number
  FRC: number
  mFTP: number
  TTE: number
  mVO2max_L_min: number
  mVO2max_ml_min_kg: number
  tau: number
  t0: number
  sub_cp_note: string
  mmp: [number, number][]  // [seconds, power]
  error?: string
}

// ─── /activities ──────────────────────────────────────────────────

export interface Activity {
  id: number
  filename: string
  sport: string
  sub_sport: string
  start_time: string
  total_elapsed_time: number
  total_timer_time: number
  total_distance: number
  avg_power: number | null
  max_power: number | null
  normalized_power: number | null
  intensity_factor: number | null
  training_stress_score: number | null
  avg_heart_rate: number | null
  max_heart_rate: number | null
  avg_cadence: number | null
  avg_speed: number | null
  total_ascent: number | null
  total_calories: number | null
}

export interface ActivitiesResponse {
  activities: Activity[]
  total: number
  limit: number
  offset: number
}

// ─── /rolling-ftp ─────────────────────────────────────────────────

export interface RollingFtpRow {
  date: string
  mFTP: number
  Pmax: number
  FRC: number
  TTE_min: number
}

// ─── /ftp-growth ──────────────────────────────────────────────────

export interface FtpGrowthResponse {
  slope: number
  intercept: number
  r_squared: number
  improvement_rate_w_per_year: number
  plateau_detected: boolean
  growth_phase: string
  training_age_weeks: number
  data_points: { date: string; mFTP: number }[]
  error?: string
}

// ─── /rolling-pd-profile ──────────────────────────────────────────

export interface RollingPdRow {
  date: string
  mFTP: number
  Pmax: number
  FRC: number
  TTE: number
}

export interface RollingPdResponse {
  data: RollingPdRow[]
}

// ─── /if-distribution ─────────────────────────────────────────────

export interface IfDistributionResponse {
  histogram: Record<string, number>
  floor: number
  ceiling: number
  spread: number
  compressed: boolean
  rides_analyzed: number
}

// ─── /fresh-baseline ──────────────────────────────────────────────

export interface FreshBaselineEntry {
  exists: boolean
  value: number | null
  date: string | null
  staleness_days: number | null
}

export type FreshBaselineResponse = Record<string, FreshBaselineEntry>

// ─── /short-power-consistency ─────────────────────────────────────

export interface ShortPowerResponse {
  peak: number
  typical: number
  ratio: number
  diagnosis: string
  efforts_analyzed: number
  message: string
}

// ─── /performance-trend ───────────────────────────────────────────

export interface PerformanceTrendRow {
  date: string
  metric: string
  value: number
}

export interface PerformanceTrendResponse {
  data: PerformanceTrendRow[]
}

// ─── /detect-phase ────────────────────────────────────────────────

export interface DetectedPhase {
  phase: string
  confidence: number
  reasoning: string
}

// ─── /feasibility ─────────────────────────────────────────────────

export interface FeasibilityResponse {
  current_ctl: number
  target_ctl: number
  ctl_gap: number
  weeks_available: number
  required_ramp_rate: number
  max_sustainable_ramp: number
  feasible: boolean
  margin_weeks: number
}

// ─── /training-blocks ─────────────────────────────────────────────

export interface TrainingBlock {
  start: string
  end: string
  volume: number
  intensity: number
  power: number
  tp: number
}

// ─── /weekly-summary ──────────────────────────────────────────────

export interface WeeklySummary {
  week: string
  hours: number
  km: number
  tss: number
  ride_count: number
  avg_if: number
  elevation: number
  avg_power: number
}

// ─── /posterior-summary ───────────────────────────────────────────

export interface PosteriorParam {
  median: number
  ci_95: [number, number]
  std: number
  ci_width: number
}

export interface PosteriorSummaryResponse {
  pd_model: Record<string, PosteriorParam>
  durability: Record<string, PosteriorParam>
}

// ─── /ride/{id} ───────────────────────────────────────────────────

export interface RideSummary {
  id: number
  filename: string
  sport: string
  start_time: string
  total_elapsed_time: number
  total_timer_time: number
  total_distance: number
  avg_power: number | null
  max_power: number | null
  normalized_power: number | null
  intensity_factor: number | null
  training_stress_score: number | null
  avg_heart_rate: number | null
  max_heart_rate: number | null
}

export interface RideRecord {
  elapsed_seconds: number
  power: number | null
  heart_rate: number | null
  cadence: number | null
  speed: number | null
  altitude: number | null
}

export interface RideInterval {
  start: number
  end: number
  avg_power: number
  max_power: number
  avg_hr: number | null
  duration: number
}

export interface RideDetail {
  summary: RideSummary
  records: RideRecord[]
  intervals: RideInterval[]
  error?: string
}

// ─── /routes ──────────────────────────────────────────────────────

export interface RouteListItem {
  id: number
  name: string
  distance_km: number
  elevation_m: number
  source: string
}

export interface RoutePoint {
  lat: number
  lon: number
  elevation: number
  km: number
}

export interface RouteDetail {
  id: number
  name: string
  distance_km: number
  elevation_m: number
  source: string
  history: Record<string, unknown>[]
  plans: Record<string, unknown>[]
  points: RoutePoint[]
}

// ─── /glycogen-budget (POST) ──────────────────────────────────────

export interface GlycogenBudgetRequest {
  ride_kj: number
  ride_duration_h: number
  on_bike_carbs_g: number
  post_ride_delay_h: number
  daily_carb_target_g_kg: number
  weight_kg: number
}

export interface GlycogenBudgetResponse {
  timeline: { hour: number; glycogen_g: number }[]
  bonk_risk: boolean
  nadir_g: number
  nadir_hour: number
  recovery_hours: number
}

// ─── Annotations (MCP) ───────────────────────────────────────────

export interface Annotation {
  id: string
  source: 'claude' | 'user'
  type: 'region' | 'line' | 'point'
  x?: [string, string] | string
  y?: number
  label: string
  color: string
  timestamp: string
}
