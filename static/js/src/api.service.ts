import { ModelInfo, ProcessedFile, ChatResponse, Config, ApiError } from './types';

export class ApiService {
  private static instance: ApiService;
  private csrfToken: string;

  private constructor() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    this.csrfToken = metaTag ? metaTag.getAttribute('content') || '' : '';
  }

  public static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService();
    }
    return ApiService.instance;
  }

  private getHeaders(isFormData: boolean = false): HeadersInit {
    const headers: HeadersInit = {
      'X-CSRFToken': this.csrfToken,
    };

    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.message || error.error || 'An error occurred');
    }
    return response.json();
  }

  public async getModelInfo(): Promise<ModelInfo> {
    const response = await fetch('/model-info', {
      headers: this.getHeaders(),
    });
    return this.handleResponse<ModelInfo>(response);
  }

  public async getProcessedFiles(): Promise<ProcessedFile[]> {
    const response = await fetch('/processed-files', {
      headers: this.getHeaders(),
    });
    return this.handleResponse<ProcessedFile[]>(response);
  }

  public async uploadPdf(file: File): Promise<{ message: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/upload', {
      method: 'POST',
      headers: {
        'X-CSRFToken': this.csrfToken,
      },
      body: formData,
    });
    return this.handleResponse<{ message: string }>(response);
  }

  public async sendMessage(message: string): Promise<ChatResponse> {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ message }),
    });
    return this.handleResponse<ChatResponse>(response);
  }

  public async saveConfig(config: Config): Promise<{ status: string }> {
    const response = await fetch('/save-config', {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(config),
    });
    return this.handleResponse<{ status: string }>(response);
  }

  public async resetConfig(): Promise<Config> {
    const response = await fetch('/reset-config', {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return this.handleResponse<Config>(response);
  }
}
