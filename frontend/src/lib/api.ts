import axios from "axios";
import type {
  AnalyzeRequest,
  AnalyzeResponse,
  EvalResult,
  ExampleNote,
  HealthResponse,
} from "../types/api";

const baseURL = import.meta.env.VITE_API_BASE ?? "/api";

const client = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await client.get<HealthResponse>("/health");
  return data;
}

export async function analyze(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const { data } = await client.post<AnalyzeResponse>("/analyze", request);
  return data;
}

export async function getExamples(): Promise<ExampleNote[]> {
  const { data } = await client.get<ExampleNote[]>("/examples");
  return data;
}

export async function getRandomNote(): Promise<ExampleNote> {
  const { data } = await client.get<ExampleNote>("/mtsamples/random");
  return data;
}

export async function getEval(): Promise<EvalResult[]> {
  const { data } = await client.get<EvalResult[]>("/eval");
  return data;
}
