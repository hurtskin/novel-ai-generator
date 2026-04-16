import React, { useEffect } from 'react';
import { useAppStore } from './stores/appStore';
import { apiClient } from './api/client';
import { DebugPanel } from './components/DebugPanel';
import { ChatPanel } from './components/ChatPanel';
import { SettingsPanel } from './components/SettingsPanel';
import { ProgressPanel } from './components/ProgressPanel';
import { InterventionPanel } from './components/InterventionPanel';

const panelConfig = [
  { id: 'progress', label: '进度', icon: '📊' },
  { id: 'debug', label: '调试', icon: '🔧' },
  { id: 'intervention', label: '介入', icon: '✋' },
  { id: 'chat', label: '对话', icon: '💬' },
  { id: 'settings', label: '设置', icon: '⚙️' },
] as const;

export const App: React.FC = () => {
  const { 
    connectionStatus, 
    selectedPanel, 
    setSelectedPanel, 
    setConnectionStatus,
    addLog,
    addNodeMetric,
    addChapterMetric,
    setTotalMetrics,
    setProgress,
    addChatMessage,
    setMemories,
    error,
    setError,
    setConfig,
    config,
    setInterventionData,
  } = useAppStore();

  useEffect(() => {
    let retryCount = 0;
    const maxRetries = 3;

    const loadConfig = async () => {
      try {
        const cfg = await apiClient.getConfig();
        setConfig(cfg);
      } catch (e) {
        console.error('Failed to load config:', e);
      }
    };

    const unsubConnected = apiClient.on('connected', async () => {
      setConnectionStatus('connected');
      loadConfig();
      try {
        const status = await apiClient.status();
        if (status.is_running || status.is_paused) {
          let progressStatus: 'idle' | 'running' | 'paused' | 'stopped' | 'completed' = 'idle';
          if (status.is_stopped) {
            progressStatus = 'stopped';
          } else if (status.is_paused) {
            progressStatus = 'paused';
          } else if (status.is_running) {
            progressStatus = 'running';
          }
          setProgress({
            current_chapter: status.current_chapter || 0,
            total_chapters: status.total_chapters || 0,
            current_node: '',
            total_nodes: 0,
            status: progressStatus,
            is_paused: status.is_paused || false,
            estimated_remaining_time_min: 0,
            estimated_remaining_cost_usd: 0,
          });
        }
      } catch (e) {
        console.error('Failed to fetch status:', e);
      }
    });

    const unsubDisconnected = apiClient.on('disconnected', () => {
      setConnectionStatus('disconnected');
      handleConnectionError();
    });

    const unsubLog = apiClient.on('log', (data: any) => {
      addLog(data);
    });

    const unsubNodeMetric = apiClient.on('node_metric', (data: any) => {
      addNodeMetric(data);
    });

    const unsubChapterMetric = apiClient.on('chapter_metric', (data: any) => {
      addChapterMetric(data);
    });

    const unsubTotalMetric = apiClient.on('total_metric', (data: any) => {
      setTotalMetrics(data);
    });

    const unsubProgress = apiClient.on('progress', (data: any) => {
      setProgress({
        current_chapter: data.current || 0,
        total_chapters: data.total || 0,
        current_node: data.current_node || '',
        total_nodes: 0,
        status: 'running',
        is_paused: false,
        estimated_remaining_time_min: 0,
        estimated_remaining_cost_usd: data.estimated_remaining_cost || 0,
      });
    });

    const unsubStatus = apiClient.on('status', (data: any) => {
      if (data.is_running === false) {
        setProgress({
          status: data.is_stopped ? 'stopped' : 'completed',
          is_paused: false,
        });
      }
      if (data.need_human_intervention) {
        setInterventionData({
          needIntervention: true,
          versions: data.intervention_data?.versions || [],
          nodeId: data.current_node || '',
          chapterId: data.current_chapter || 0,
        });
        setSelectedPanel('intervention');
      } else if (selectedPanel === 'intervention' && !data.need_human_intervention) {
        setInterventionData(null);
      }
    });

    const unsubComplete = apiClient.on('complete', () => {
      setProgress({
        status: 'completed',
        is_paused: false,
      });
    });

    const unsubChat = apiClient.on('chat', (data: any) => {
      addChatMessage(data);
    });

    const unsubMemory = apiClient.on('memory', (data: any) => {
      setMemories(data);
    });

    const unsubError = apiClient.on('error', (data: any) => {
      setError(data.message || 'Unknown error');
    });

    const handleConnectionError = () => {
      if (retryCount < maxRetries) {
        retryCount++;
        setTimeout(() => {
          setConnectionStatus('connecting');
          apiClient.connect();
        }, 2000);
      } else {
        setConnectionStatus('disconnected');
        setError('无法连接到后端服务 (端口 8000)。请确保后端正在运行: python main.py');
      }
    };

    const tryConnect = () => {
      setConnectionStatus('connecting');
      apiClient.connect();
    };

    tryConnect();

    return () => {
      unsubConnected();
      unsubDisconnected();
      unsubLog();
      unsubNodeMetric();
      unsubChapterMetric();
      unsubTotalMetric();
      unsubProgress();
      unsubStatus();
      unsubComplete();
      unsubChat();
      unsubMemory();
      unsubError();
      apiClient.disconnect();
    };
  }, []);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  useEffect(() => {
    if (config?.ui) {
      const uiTheme = config.ui.theme || 'dark';
      document.documentElement.setAttribute('data-theme', uiTheme);
    }
  }, [config?.ui?.theme]);

  const renderPanel = () => {
    switch (selectedPanel) {
      case 'progress': return <ProgressPanel />;
      case 'debug': return <DebugPanel key="debug" />;
      case 'intervention': return <InterventionPanel />;
      case 'chat': return <ChatPanel />;
      case 'settings': return <SettingsPanel />;
      default: return <ProgressPanel />;
    }
  };

  const theme = config?.ui?.theme || 'dark';
  const colors = theme === 'light' ? {
    bg: '#f5f5f5',
    bgSecondary: '#fff',
    text: '#333',
    border: '#ddd',
    textSecondary: '#666',
  } : {
    bg: '#1e1e1e',
    bgSecondary: '#2d2d2d',
    text: '#fff',
    border: '#333',
    textSecondary: '#888',
  };

  const statusColors = {
    connected: '#198754',
    connecting: '#ffc107',
    disconnected: '#dc3545',
  };

  return (
    <div style={{ ...containerStyle, background: colors.bg, color: colors.text }}>
      <header style={{ ...headerStyle, background: colors.bgSecondary, borderColor: colors.border }}>
        <div style={titleStyle}>
          <span style={{ fontSize: '20px' }}>📖</span>
          <span>NovelAI - 多文体AI生成框架</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ 
              width: '8px', 
              height: '8px', 
              borderRadius: '50%', 
              background: statusColors[connectionStatus] 
            }} />
            <span style={{ fontSize: '12px', color: colors.textSecondary }}>
              {connectionStatus === 'connected' ? '已连接' : 
               connectionStatus === 'connecting' ? '连接中...' : '未连接'}
            </span>
          </div>
        </div>
      </header>

      <nav style={{ ...navStyle, background: colors.bgSecondary, borderColor: colors.border }}>
        {panelConfig.map((panel) => (
          <button
            key={panel.id}
            onClick={() => setSelectedPanel(panel.id)}
            style={{
              ...navBtnStyle,
              ...(selectedPanel === panel.id ? activeNavBtnStyle : {}),
              color: selectedPanel === panel.id ? '#fff' : colors.textSecondary,
            }}
          >
            <span>{panel.icon}</span>
            <span>{panel.label}</span>
          </button>
        ))}
      </nav>

      <main style={{ ...mainStyle, background: colors.bg }}>
        {error && (
          <div style={errorToastStyle}>
            {error}
            <button onClick={() => setError(null)} style={closeBtnStyle}>×</button>
          </div>
        )}
        {renderPanel()}
      </main>
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  height: '100vh',
  background: '#1e1e1e',
  color: '#fff',
  fontFamily: 'system-ui, -apple-system, sans-serif',
};

const headerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '12px 24px',
  background: '#2d2d2d',
  borderBottom: '1px solid #333',
};

const titleStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  fontSize: '16px',
  fontWeight: 'bold',
};

const navStyle: React.CSSProperties = {
  display: 'flex',
  padding: '8px 24px',
  background: '#252525',
  borderBottom: '1px solid #333',
  gap: '8px',
};

const navBtnStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '8px 16px',
  background: 'transparent',
  color: '#888',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '14px',
  transition: 'all 0.2s',
};

const activeNavBtnStyle: React.CSSProperties = {
  background: '#0d6efd',
  color: '#fff',
};

const mainStyle: React.CSSProperties = {
  flex: 1,
  padding: '24px',
  overflow: 'hidden',
};

const errorToastStyle: React.CSSProperties = {
  position: 'absolute',
  top: '80px',
  right: '24px',
  padding: '12px 16px',
  background: '#dc3545',
  color: '#fff',
  borderRadius: '4px',
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  zIndex: 1000,
  animation: 'slideIn 0.3s ease',
};

const closeBtnStyle: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  color: '#fff',
  fontSize: '18px',
  cursor: 'pointer',
};

export default App;
