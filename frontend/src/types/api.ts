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

export interface AnalyzeResponse {
  deid_redactions: number;
  deid_text: string;
  sections: Section[];
  phi_spans: PhiSpan[];
  entities: Entity[];
  gaps: HccGap[];
  risk_score: number;
  risk_score_current: number;
  risk_score_potential: number;
  risk_score_delta: number;
  demographics: PatientDemographics;
  fhir_bundle: Record<string, unknown>;
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
