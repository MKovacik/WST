import { ApiService } from './api.service.js';
import { UiService } from './ui.service.js';
import { Config } from './types.js';

export class App {
  private static instance: App;
  private apiService: ApiService;
  private uiService: UiService;

  private constructor() {
    console.log('Initializing App...');
    this.apiService = ApiService.getInstance();
    this.uiService = UiService.getInstance();
    this.init();
  }

  public static getInstance(): App {
    if (!App.instance) {
      console.log('Creating new App instance');
      App.instance = new App();
    }
    return App.instance;
  }

  private init(): void {
    console.log('Setting up event listeners...');
    document.addEventListener('DOMContentLoaded', () => {
      console.log('DOM loaded, initializing app features...');
      this.loadProcessedFiles();
      this.loadModelInfo();
      this.setupEventListeners();
      this.setupRangeSliders();
      
      // Direct DOM manipulation for toggle functionality
      const toggleConfigBtn = document.getElementById('toggleConfigBtn');
      const configContent = document.getElementById('configContent');
      
      if (toggleConfigBtn && configContent) {
        // Initially hide the config content
        configContent.classList.remove('active');
        
        // Add click handler to toggle button
        toggleConfigBtn.onclick = function(event) {
          console.log('Toggle button clicked directly');
          event.stopPropagation(); // Prevent event bubbling
          configContent.classList.toggle('active');
          return false; // Prevent default action
        };
      }
      
      // Direct handlers for save and reset buttons
      const saveConfigBtn = document.getElementById('saveConfigBtn');
      if (saveConfigBtn) {
        saveConfigBtn.onclick = () => {
          console.log('Save button clicked directly');
          this.handleSaveConfig();
          return false;
        };
      }
      
      const resetConfigBtn = document.getElementById('resetConfigBtn');
      if (resetConfigBtn) {
        resetConfigBtn.onclick = () => {
          console.log('Reset button clicked directly');
          this.handleResetConfig();
          return false;
        };
      }
    });
  }

  private setupEventListeners(): void {
    // Upload button
    const uploadButton = document.getElementById('uploadButton');
    if (uploadButton) {
      uploadButton.addEventListener('click', () => this.handleUpload());
    }

    // Send message button
    const sendButton = document.getElementById('sendButton');
    if (sendButton) {
      sendButton.addEventListener('click', () => this.handleSendMessage());
    }

    // Enter key in input
    const userInput = document.getElementById('userInput');
    if (userInput) {
      userInput.addEventListener('keypress', (event: KeyboardEvent) => {
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          this.handleSendMessage();
        }
      });
    }

    // Config panel toggle
    const toggleConfigBtn = document.getElementById('toggleConfigBtn');
    if (toggleConfigBtn) {
      toggleConfigBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.uiService.toggleConfigPanel();
      });
    }

    // Config header toggle
    const configHeader = document.getElementById('toggleConfigHeader');
    if (configHeader) {
      configHeader.addEventListener('click', () => this.uiService.toggleConfigPanel());
    }

    // Debug info toggle
    const debugToggleBtn = document.getElementById('debugToggleBtn');
    if (debugToggleBtn) {
      debugToggleBtn.addEventListener('click', () => this.uiService.toggleDebugInfo());
    }

    // Save config button - Direct implementation with event delegation
    const saveConfigBtn = document.getElementById('saveConfigBtn');
    if (saveConfigBtn) {
      saveConfigBtn.onclick = (e) => {
        e.stopPropagation();
        console.log('Save config button clicked - using onclick');
        this.handleSaveConfig();
        return false;
      };
    }

    // Reset config button - Direct implementation with event delegation
    const resetConfigBtn = document.getElementById('resetConfigBtn');
    if (resetConfigBtn) {
      resetConfigBtn.onclick = (e) => {
        e.stopPropagation();
        console.log('Reset config button clicked - using onclick');
        this.handleResetConfig();
        return false;
      };
    }
  }

  private setupRangeSliders(): void {
    const sliders = {
      temperature: document.getElementById('temperature') as HTMLInputElement,
      maxTokens: document.getElementById('maxTokens') as HTMLInputElement,
      topP: document.getElementById('topP') as HTMLInputElement,
      contextChunks: document.getElementById('contextChunks') as HTMLInputElement,
    };

    Object.entries(sliders).forEach(([id, slider]) => {
      if (slider) {
        slider.addEventListener('input', () => {
          this.uiService.updateConfigValue(id, slider.value);
        });
      }
    });
  }

  private async loadModelInfo(): Promise<void> {
    try {
      const modelInfo = await this.apiService.getModelInfo();
      this.uiService.updateModelInfo(modelInfo);
      console.log('Model info loaded successfully');
    } catch (error) {
      console.error('Error loading model info:', error);
      const maxTokensInfo = document.getElementById('maxTokensInfo');
      if (maxTokensInfo) {
        maxTokensInfo.textContent = 'Could not fetch model information';
        maxTokensInfo.style.color = '#dc3545';
      }
    }
  }

  private async loadProcessedFiles(): Promise<void> {
    try {
      const files = await this.apiService.getProcessedFiles();
      this.uiService.updateFileList(files);
    } catch (error) {
      console.error('Error loading processed files:', error);
    }
  }

  private async handleUpload(): Promise<void> {
    const fileInput = document.getElementById('pdfFile') as HTMLInputElement;
    const file = fileInput.files?.[0];

    if (!file) {
      alert('Please select a file first.');
      return;
    }

    this.uiService.setLoading('upload', true);

    try {
      await this.apiService.uploadPdf(file);
      await this.loadProcessedFiles();
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error uploading file: ' + error);
    } finally {
      this.uiService.setLoading('upload', false);
    }
  }

  private async handleSendMessage(): Promise<void> {
    const message = this.uiService.getUserInput();
    if (!message) return;

    this.uiService.clearInput();
    this.uiService.addMessage(message, true);
    this.uiService.showTypingIndicator();
    this.uiService.setLoading('send', true);

    try {
      const response = await this.apiService.sendMessage(message);
      this.uiService.removeTypingIndicator();

      if (response.error) {
        this.uiService.showError(response.error);
      } else {
        this.uiService.addMessage(response.response, false);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      this.uiService.removeTypingIndicator();
      this.uiService.showError('Failed to send message');
    } finally {
      this.uiService.setLoading('send', false);
    }
  }

  private toggleConfigPanel(): void {
    const configPanel = document.getElementById('configPanel');
    if (configPanel) {
      configPanel.style.display = configPanel.style.display === 'none' ? 'block' : 'none';
    }
  }

  private async handleSaveConfig(): Promise<void> {
    const config: Config = {
      temperature: parseFloat((document.getElementById('temperature') as HTMLInputElement).value),
      max_tokens: parseInt((document.getElementById('maxTokens') as HTMLInputElement).value),
      top_p: parseFloat((document.getElementById('topP') as HTMLInputElement).value),
      context_chunks: parseInt(
        (document.getElementById('contextChunks') as HTMLInputElement).value
      ),
      system_prompt: (document.getElementById('systemPrompt') as HTMLTextAreaElement).value,
    };

    try {
      await this.apiService.saveConfig(config);
      alert('Configuration saved successfully');
    } catch (error) {
      console.error('Error saving config:', error);
      alert('Error saving configuration');
    }
  }

  private async handleResetConfig(): Promise<void> {
    try {
      const config = await this.apiService.resetConfig();

      // Update UI with reset values
      Object.entries(config).forEach(([key, value]) => {
        const element = document.getElementById(key);
        if (element) {
          if (element instanceof HTMLInputElement) {
            element.value = value.toString();
            this.uiService.updateConfigValue(key, value);
          } else if (element instanceof HTMLTextAreaElement) {
            element.value = value.toString();
          }
        }
      });

      alert('Configuration reset to defaults');
    } catch (error) {
      console.error('Error resetting config:', error);
      alert('Error resetting configuration');
    }
  }
}

// Initialize the application
App.getInstance();
