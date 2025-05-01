import { ProcessedFile, ChatMessage } from './types.js';

// Use the global hljs object since we're loading it from CDN
declare const hljs: any;

export class UiService {
  private static instance: UiService;
  private messagesContainer: HTMLElement;
  private userInput: HTMLInputElement;
  private fileList: HTMLElement;
  private configPanel: HTMLElement;
  private maxTokensSlider: HTMLInputElement;
  private maxTokensInfo: HTMLElement;
  private apiDebug: HTMLElement;

  private constructor() {
    console.log('Initializing UI Service...');
    this.messagesContainer = document.getElementById('messages') as HTMLElement;
    this.userInput = document.getElementById('userInput') as HTMLInputElement;
    this.fileList = document.getElementById('fileList') as HTMLElement;
    this.configPanel = document.getElementById('configPanel') as HTMLElement;
    this.maxTokensSlider = document.getElementById('maxTokens') as HTMLInputElement;
    this.maxTokensInfo = document.getElementById('maxTokensInfo') as HTMLElement;
    this.apiDebug = document.getElementById('apiDebug') as HTMLElement;

    // Initialize config panel state
    if (this.configPanel) {
      this.configPanel.style.display = 'none';
    }

    // Initialize debug info state
    if (this.apiDebug) {
      this.apiDebug.style.display = 'none';
    }
  }

  public static getInstance(): UiService {
    if (!UiService.instance) {
      UiService.instance = new UiService();
    }
    return UiService.instance;
  }

  public showTypingIndicator(): void {
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.id = 'typingIndicator';

    for (let i = 0; i < 3; i++) {
      const dot = document.createElement('div');
      dot.className = 'typing-dot';
      indicator.appendChild(dot);
    }

    this.messagesContainer.appendChild(indicator);
    this.scrollToBottom();
  }

  public removeTypingIndicator(): void {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
      indicator.remove();
    }
  }

  public addMessage(content: string, isUser: boolean): void {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;

    if (isUser) {
      messageDiv.textContent = content;
    } else {
      // Process markdown and add to message
      messageDiv.innerHTML = content;

      // Highlight code blocks
      messageDiv.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block as HTMLElement);
      });
    }

    this.messagesContainer.appendChild(messageDiv);
    this.scrollToBottom();
  }

  public showError(message: string): void {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'message error';
    errorDiv.textContent = message;
    this.messagesContainer.appendChild(errorDiv);
    this.scrollToBottom();
  }

  public updateFileList(files: ProcessedFile[]): void {
    this.fileList.innerHTML = '';

    if (files.length === 0) {
      this.fileList.innerHTML = '<li class="file-item">No files processed yet</li>';
      return;
    }

    files.forEach((file) => {
      const li = document.createElement('li');
      li.className = 'file-item';

      const date = new Date(file.processed_at);
      const formattedDate = date.toLocaleString();

      li.innerHTML = `
                <span class="file-icon">
                    <i class="fas fa-file-pdf"></i>
                </span>
                <div class="file-details">
                    <div class="file-name">${file.filename}</div>
                    <div class="file-meta">
                        ${file.pages} pages · ${file.chunks} chunks · Processed: ${formattedDate}
                    </div>
                </div>
            `;

      this.fileList.appendChild(li);
    });
  }

  public setLoading(type: 'upload' | 'send', isLoading: boolean): void {
    const button = document.getElementById(
      type === 'upload' ? 'uploadButton' : 'sendButton'
    ) as HTMLButtonElement;
    const overlay = document.getElementById(
      type === 'upload' ? 'uploadLoadingOverlay' : 'sendLoadingOverlay'
    ) as HTMLElement;

    if (button && overlay) {
      button.disabled = isLoading;
      overlay.classList.toggle('active', isLoading);
    }
  }

  public toggleConfigPanel(): void {
    console.log('Toggling config panel');
    if (this.configPanel) {
      this.configPanel.style.display = this.configPanel.style.display === 'none' ? 'block' : 'none';
    }
  }

  public toggleDebugInfo(): void {
    console.log('Toggling debug info');
    if (this.apiDebug) {
      this.apiDebug.style.display = this.apiDebug.style.display === 'none' ? 'block' : 'none';
    }
  }

  public updateConfigValue(id: string, value: string | number): void {
    const element = document.getElementById(`${id}Value`);
    if (element) {
      element.textContent = value.toString();
    }
  }

  public clearInput(): void {
    this.userInput.value = '';
  }

  public getUserInput(): string {
    return this.userInput.value.trim();
  }

  public updateModelInfo(modelInfo: any): void {
    console.log('Updating model info:', modelInfo);

    const modelName = document.getElementById('modelName');
    if (modelName) {
      modelName.textContent = modelInfo.model_name;
    }

    // Update max tokens slider
    if (this.maxTokensSlider && modelInfo.max_tokens) {
      this.maxTokensSlider.max = modelInfo.max_tokens.toString();

      // Update step size based on max tokens
      if (modelInfo.max_tokens > 8000) {
        this.maxTokensSlider.step = '1000';
      } else if (modelInfo.max_tokens > 4000) {
        this.maxTokensSlider.step = '500';
      } else {
        this.maxTokensSlider.step = '100';
      }

      // Show model's max tokens in the info text
      if (this.maxTokensInfo) {
        this.maxTokensInfo.textContent = `Model maximum: ${modelInfo.max_tokens.toLocaleString()} tokens`;
        this.maxTokensInfo.style.color = '#6c757d';
      }
    }

    // Update debug info
    const apiDebug = document.getElementById('apiDebug');
    if (apiDebug) {
      apiDebug.textContent = JSON.stringify(modelInfo, null, 2);
    }
  }

  private scrollToBottom(): void {
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }
}
