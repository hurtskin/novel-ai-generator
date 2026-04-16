const API_BASE = 'http://127.0.0.1:8000';

export interface LogEntry {
  timestamp: string;
  level: string;
  chapter: number;
  node: string;
  message: string;
}

export interface NodeMetric {
  node_id: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  ttf_ms: number;
  tps: number;
  duration_ms: number;
  api_latency_ms: number;
  retry_count: number;
  cost_usd: number;
}

export interface ChapterMetric {
  chapter_id: number;
  total_nodes: number;
  total_duration_ms: number;
  total_tokens: number;
  avg_tps: number;
  total_retries: number;
  total_cost_usd: number;
}

export interface TotalMetric {
  total_chapters: number;
  total_duration_min: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_chapter_time_min: number;
}

export interface ProgressData {
  current_chapter: number;
  total_chapters: number;
  current_node: string;
  total_nodes: number;
  status: 'idle' | 'running' | 'paused' | 'stopped' | 'completed';
  is_paused: boolean;
  estimated_remaining_time_min: number;
  estimated_remaining_cost_usd: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  chapter?: number;
  node?: string;
}

export interface MemoryFragment {
  id: string;
  content: string;
  chapter: number;
  node: string;
  timestamp: string;
}

export interface AppConfig {
  api: {
    base_url: string;
    api_key: string;
    model: string;
    timeout: number;
    max_retries: number;
    provider?: string;
  };
  ollama?: {
    enabled: boolean;
    base_url: string;
    model: string;
    timeout: number;
  };
  generation: {
    temperature: number;
    top_p: number;
    max_tokens: number;
  };
  ui: {
    font_family: string;
    font_size: number;
    theme: 'dark' | 'light';
    language: 'zh-CN' | 'en';
  };
  performance: {
    cost_alert_usd: number;
  };
  genre: 'novel' | 'script' | 'game_story' | 'dialogue' | 'article';
}

export class ApiClient {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  async start(theme: string, style: string = 'novel', total_words: number = 10000, character_count: number = 3): Promise<{ task_id: string }> {
    const res = await fetch(`${API_BASE}/api/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theme, style, total_words, character_count }),
    });
    return res.json();
  }

  async status(): Promise<{
    is_running: boolean;
    is_paused: boolean;
    is_stopped: boolean;
    current_chapter: number;
    current_node: string;
    total_chapters: number;
    error: string | null;
    novel_content: string;
  }> {
    const res = await fetch(`${API_BASE}/api/status`);
    return res.json();
  }

  async pause(): Promise<void> {
    await fetch(`${API_BASE}/api/pause`, { method: 'POST' });
  }

  async resume(): Promise<void> {
    await fetch(`${API_BASE}/api/resume`, { method: 'POST' });
  }

  async selectVersion(versionIndex: number): Promise<void> {
    await fetch(`${API_BASE}/api/select_version`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ version_index: versionIndex }),
    });
  }

  async retryNode(): Promise<void> {
    await fetch(`${API_BASE}/api/retry_node`, { method: 'POST' });
  }

  async stop(): Promise<void> {
    await fetch(`${API_BASE}/api/stop`, { method: 'POST' });
  }

  async regenerate(chapter_id: number, node_id: string): Promise<void> {
    await fetch(`${API_BASE}/api/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chapter_id, node_id }),
    });
  }

  async getSnapshots(): Promise<{ snapshots: string[] }> {
    const res = await fetch(`${API_BASE}/api/snapshots`);
    return res.json();
  }

  async getSnapshot(name: string): Promise<{ status: string; snapshot?: any; message?: string }> {
    const res = await fetch(`${API_BASE}/api/snapshot/${name}`);
    return res.json();
  }

  async saveSnapshot(name: string): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/api/snapshot/${name}`, {
      method: 'POST',
    });
    return res.json();
  }

  async getPerformance(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/performance`);
    return res.json();
  }

  async saveConfig(config: AppConfig): Promise<void> {
    await fetch(`${API_BASE}/api/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
  }

  async getConfig(): Promise<AppConfig> {
    const res = await fetch(`${API_BASE}/api/config`);
    return res.json();
  }

  async getDebugLog(): Promise<{ content: string; exists: boolean }> {
    const res = await fetch(`${API_BASE}/api/debuglog`);
    return res.json();
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already open, skipping');
      return;
    }

    const wsUrl = API_BASE.replace('http://', 'ws://').replace('https://', 'ws://') + '/api/stream';
    console.log('Creating WebSocket connection to:', wsUrl);

    fetch('http://127.0.0.1:8000/api/status')
      .then((response) => {
        if (!response.ok) {
          throw new Error('HTTP check failed');
        }
        console.log('HTTP check OK, trying WebSocket...');
        return response.json();
      })
      .then(() => {
        try {
          const ws = new WebSocket(wsUrl);
          this.ws = ws;

          ws.onerror = (error) => {
            console.error('WebSocket onerror:', error);
            console.error('WebSocket readyState:', ws.readyState);
            console.error('WebSocket url:', ws.url);
            this.emit('error', error);
          };

          ws.onopen = () => {
            console.log('WebSocket onopen fired, readyState:', ws.readyState);
            this.emit('connected', {});
          };

          ws.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data);
              console.log('WebSocket message received:', data);
              if (data.type === 'ping') {
                this.ws?.send(JSON.stringify({ type: 'pong' }));
                return;
              }
              if (data.type === 'pong') {
                return;
              }
              const payload = data.data || data.payload || data.message || {};
              console.log('Emitting event:', data.type, 'with payload:', payload);
              this.emit(data.type, payload);
              this.emit('*', data);
            } catch (e) {
              console.error('WebSocket message parse error:', e);
            }
          };

          ws.onclose = (event) => {
            console.log('WebSocket onclose fired:', event.code, event.reason);
            this.emit('disconnected', {});
            if (event.code !== 1000) {
              setTimeout(() => this.connect(), 3000);
            }
          };
        } catch (e) {
          console.error('Failed to create WebSocket:', e);
        }
      })
      .catch((e) => {
        console.error('Backend not reachable via HTTP:', e);
      });
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }

  on(event: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
    return () => this.listeners.get(event)?.delete(callback);
  }

  private emit(event: string, data: any): void {
    this.listeners.get(event)?.forEach((cb) => cb(data));
  }
}

export const apiClient = new ApiClient();
