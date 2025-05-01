export interface ModelInfo {
  model_name: string;
  context_window: number;
  max_tokens: number;
  raw_api_response: any;
}

export interface ProcessedFile {
  filename: string;
  pages: number;
  chunks: number;
  processed_at: string;
}

export interface ChatMessage {
  content: string;
  isUser: boolean;
}

export interface ChatResponse {
  response: string;
  error?: string;
}

export interface Config {
  temperature: number;
  max_tokens: number;
  top_p: number;
  context_chunks: number;
  system_prompt: string;
}

export interface ApiError {
  error: string;
  message?: string;
}
