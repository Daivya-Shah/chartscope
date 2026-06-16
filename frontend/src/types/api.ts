export interface AnalyzeRequest {
  note_text: string;
  claimed_codes: string[];
}

export interface Entity {
  text: string;
  label: string;
  start_char: number;
  end_char: number;
  section: string | null;
  negated: boolean;
  uncertain: boolean;
  historical: boolean;
  family: boolean;
  is_active: boolean;
  drop_reason: string | null;
  score: number;
  cui?: string | null;
  icd10?: string | null;
  icd10_desc?: string | null;
  rxnorm?: string | null;
  rxnorm_name?: string | null;
  link_score?: number | null;
}

export interface HccGap {
  hcc: string;
  label: string;
  status: string;
  evidence: string;
  icd10: string;
  confidence: number;
  recommendation?: string | null;
}

export interface Section {
  name: string;
  start_char: number;
  end_char: number;
}

export interface PhiSpan {
  type: string;
  start: number;
  end: number;
}

export interface PatientDemographics {
  age: number;
  sex: string;
}

export interface KeyProblem {
  text: string;
  icd10: string;
  icd10_desc?: string | null;
  section: string | null;
  score: number;
}

export interface AnalyzeResponse {
  deid_redactions: number;
  deid_text: string;
  sections: Section[];
  phi_spans: PhiSpan[];
  entities: Entity[];
  key_problems: KeyProblem[];
  gaps: HccGap[];
  risk_score: number;
  risk_score_current: number;
  risk_score_potential: number;
  risk_score_delta: number;
  demographics: PatientDemographics;
  fhir_bundle: Record<string, unknown>;
  fhir_valid: boolean;
  fhir_errors: string[];
}

export interface ExampleNote {
  id: string;
  title: string;
  specialty: string;
  note_text: string;
  claimed_codes: string[];
  description: string;
}

export interface RandomNote {
  sample_id: string;
  specialty: string;
  description: string;
  transcription: string;
}

export interface SpecialtyCount {
  specialty: string;
  count: number;
}

export interface FinetuneEntityMetrics {
  precision: number;
  recall: number;
  f1?: number;
  "f1-score"?: number;
  support?: number;
}

export interface FinetuneMetrics {
  model: string;
  dataset: string;
  epochs: number;
  smoke: boolean;
  precision: number;
  recall: number;
  f1: number;
  per_entity: Record<string, FinetuneEntityMetrics>;
  baseline?: {
    model: string;
    dataset: string;
    split: string;
    precision: number;
    recall: number;
    f1: number;
    per_entity: Record<string, FinetuneEntityMetrics>;
  };
  comparison?: {
    finetuned_f1: number;
    baseline_f1: number;
    finetuned_advantage: number;
  };
}

/** @deprecated Legacy stub shape — use FinetuneMetrics from GET /eval */
export interface EvalResult {
  metric: string;
  value: number;
  description: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}
