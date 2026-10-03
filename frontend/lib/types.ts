export type Source = {
  id: number;
  file: string;
  title: string;
  section: string;
  snippet: string;
  score: number;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: Source[];
  status: "streaming" | "done" | "error";
  grounded: boolean;
  error?: string;
};

export type Health = {
  status: string;
  provider: "anthropic" | "openai" | "offline";
  model: string | null;
  documents: number;
  chunks: number;
};

export type DocSummary = { file: string; title: string; chunks: number };
