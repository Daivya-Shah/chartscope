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
  historical: boolean;
  family: boolean;
  cui?: string | null;
  icd10?: string | null;
  score?: number | null;
}

export interface HccGap {
  hcc: string;
  label: string;
  status: string;
  evidence: string;
  icd10: string;
  confidence: number;
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

export interface AnalyzeResponse {
  deid_redactions: number;
  deid_text: string;
  sections: Section[];
  phi_spans: PhiSpan[];
  entities: Entity[];
  gaps: HccGap[];
  risk_score: number;
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
