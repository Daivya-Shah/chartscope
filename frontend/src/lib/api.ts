import axios from "axios";
import type {
  AnalyzeRequest,
  AnalyzeResponse,
  ExampleNote,
  FinetuneMetrics,
  HealthResponse,
  RandomNote,
  SpecialtyCount,
} from "../types/api";

const baseURL = import.meta.env.VITE_API_BASE ?? "/api";

const client = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

let examplesCache: ExampleNote[] | null = null;

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await client.get<HealthResponse>("/health");
  return data;
}

export async function analyze(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const { data } = await client.post<AnalyzeResponse>("/analyze", request);
  return data;
}

export async function getExamples(): Promise<ExampleNote[]> {
  if (examplesCache) return examplesCache;
  const { data } = await client.get<ExampleNote[]>("/examples");
  examplesCache = data;
  return data;
}

export async function getRandomNote(specialty?: string): Promise<RandomNote> {
  const { data } = await client.get<RandomNote>("/mtsamples/random", {
    params: specialty ? { specialty } : undefined,
  });
  return data;
}

export async function getSpecialties(): Promise<SpecialtyCount[]> {
  const { data } = await client.get<SpecialtyCount[]>("/mtsamples/specialties");
  return data;
}

export async function getEval(): Promise<FinetuneMetrics> {
  const { data } = await client.get<FinetuneMetrics>("/eval");
  return data;
}

export function parseClaimedCodes(raw: string): string[] {
  return raw
    .split(",")
    .map((c) => c.trim().toUpperCase())
    .filter(Boolean);
}
