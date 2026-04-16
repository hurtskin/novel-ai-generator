import React, { useState } from 'react';
import { useAppStore } from '../stores/appStore';
import { apiClient } from '../api/client';

export const ProgressPanel: React.FC = () => {
  const { progress, setProgress, setError, config, connectionStatus } = useAppStore();
  const [userInput, setUserInput] = useState('');
  const [starting, setStarting] = useState(false);

  const theme = config?.ui?.theme || 'dark';
  const colors = theme === 'light' ? {
    bg: '#f5f5f5',
    bgSecondary: '#fff',
    text: '#333',
    border: '#ddd',
    textSecondary: '#666',
    cardBg: '#fff',
    inputBg: '#fff',
    accent: '#0d6efd',
  } : {
    bg: '#1e1e1e',
    bgSecondary: '#2d2d2d',
    text: '#fff',
    border: '#333',
    textSecondary: '#888',
    cardBg: '#2d2d2d',
    inputBg: '#1e1e1e',
    accent: '#0d6efd',
  };

  const isRunning = progress.status === 'running' || progress.status === 'paused';
  const costAlert = config?.performance?.cost_alert_usd || 10;
  const isCostExceeded = progress.estimated_remaining_cost_usd > costAlert;

  const chapterPercent = progress.total_chapters > 0 
    ? ((progress.current_chapter - 1) / progress.total_chapters) * 100 
    : 0;

  const statusColors: Record<string, string> = {
    idle: '#6c757d',
    running: '#0dcaf0',
    paused: '#ffc107',
    stopped: '#dc3545',
    completed: '#198754',
  };

  const statusLabels: Record<string, string> = {
    idle: '空闲',
    running: '生成中',
    paused: '已暂停',
    stopped: '已终止',
    completed: '已完成',
  };

  const handleStart = async () => {
    if (!userInput.trim()) {
      setError('请输入创作主题');
      return;
    }
    if (connectionStatus !== 'connected') {
      setError('后端未连接，请确保后端服务已启动');
      return;
    }
    setStarting(true);
    try {
      await apiClient.start(userInput, 'novel', 10000, 3);
      setProgress({ 
        status: 'running', 
        current_chapter: 1, 
        current_node: '',
        total_chapters: 0,
        total_nodes: 0,
      });
    } catch (e) {
      setError('启动失败: ' + (e as Error).message);
    } finally {
      setStarting(false);
    }
  };

  const handlePause = async () => {
    try {
      if (progress.is_paused) {
        await apiClient.resume();
        setProgress({ is_paused: false, status: 'running' });
      } else {
        await apiClient.pause();
        setProgress({ is_paused: true, status: 'paused' });
      }
    } catch (e) {
      setError('操作失败: ' + (e as Error).message);
    }
  };

  const handleStop = async () => {
    try {
      await apiClient.stop();
      setProgress({ status: 'stopped', is_paused: false });
    } catch (e) {
      setError('终止失败: ' + (e as Error).message);
    }
  };

  const handleReset = () => {
    setProgress({
      current_chapter: 0,
      total_chapters: 0,
      current_node: '',
      total_nodes: 0,
      status: 'idle',
      is_paused: false,
      estimated_remaining_time_min: 0,
      estimated_remaining_cost_usd:0,
    });
    setUserInput('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '16px', overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, color: colors.text }}>📊 生成进度</h3>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px',
          padding: '4px 12px',
          borderRadius: '16px',
          background: colors.cardBg,
          border: `1px solid ${colors.border}`,
        }}>
          <div style={{ 
            width: '8px', 
            height: '8px', 
            borderRadius: '50%', 
            background: statusColors[progress.status],
            animation: isRunning ? 'pulse 1.5s infinite' : 'none',
          }} />
          <span style={{ fontSize: '12px', color: statusColors[progress.status], fontWeight: 600 }}>
            {statusLabels[progress.status]}
          </span>
        </div>
      </div>

      {!isRunning && (
        <div style={{ ...cardStyle, background: colors.cardBg, borderColor: colors.border }}>
          <div style={{ marginBottom: '12px' }}>
            <label style={{ fontSize: '13px', color: colors.textSecondary, display: 'block', marginBottom: '8px' }}>
              创作主题
            </label>
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="输入创作主题，如：编写一个关于星际探险的科幻小说，讲述人类首次跨越银河系的壮丽旅程..."
              rows={3}
              style={{ ...inputStyle, background: colors.inputBg, color: colors.text, borderColor: colors.border, resize: 'vertical', minHeight: '80px' }}
            />
          </div>
          <button 
            onClick={handleStart} 
            disabled={starting || !userInput.trim() || connectionStatus !== 'connected'}
            style={{
              ...startBtnStyle,
              opacity: starting || !userInput.trim() || connectionStatus !== 'connected' ? 0.6 : 1,
            }}
          >
            {starting ? '🚀 启动中...' : connectionStatus !== 'connected' ? '⚠️ 后端未连接' : '🚀 开始生成'}
          </button>
        </div>
      )}

      {isRunning && (
        <>
          <div style={{ ...cardStyle, background: colors.cardBg, borderColor: colors.border }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', color: colors.textSecondary }}>当前主题</span>
              <span style={{ fontSize: '13px', color: colors.text, maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {userInput}
              </span>
            </div>
            <div style={{ fontSize: '12px', color: colors.textSecondary }}>
              第 {progress.current_chapter} 章 · 第 {progress.current_node} 节点
            </div>
          </div>

          <div style={{ ...cardStyle, background: colors.cardBg, borderColor: colors.border }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', color: colors.textSecondary }}>章节进度</span>
              <span style={{ fontSize: '13px', color: colors.text }}>
                {progress.current_chapter} / {progress.total_chapters || '?'}
              </span>
            </div>
            <div style={progressBarContainerStyle}>
              <div style={{ ...progressBarFillStyle, width: `${chapterPercent}%`, background: colors.accent }} />
            </div>
          </div>

          <div style={{ ...cardStyle, background: colors.cardBg, borderColor: colors.border }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', color: colors.textSecondary }}>当前节点</span>
              <span style={{ fontSize: '13px', color: colors.text, fontWeight: 600 }}>
                {progress.current_node || '初始化中...'}
              </span>
            </div>
            <div style={{ fontSize: '12px', color: colors.textSecondary }}>
              节点 {progress.current_node ? '执行中' : '等待中'}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ ...cardStyle, background: colors.cardBg, borderColor: colors.border }}>
              <div style={{ fontSize: '11px', color: colors.textSecondary, marginBottom: '4px' }}>预估剩余时间</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: colors.text }}>
                {progress.estimated_remaining_time_min > 0 
                  ? `${progress.estimated_remaining_time_min.toFixed(1)} min` 
                  : '--'}
              </div>
            </div>
            <div style={{ ...cardStyle, background: colors.cardBg, borderColor: colors.border }}>
              <div style={{ fontSize: '11px', color: colors.textSecondary, marginBottom: '4px' }}>预估成本</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: isCostExceeded ? '#dc3545' : '#198754' }}>
                ${progress.estimated_remaining_cost_usd.toFixed(4)}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button 
              onClick={handlePause}
              style={{
                ...controlBtnStyle,
                background: progress.is_paused ? '#198754' : '#ffc107',
                color: progress.is_paused ? '#fff' : '#000',
              }}
            >
              {progress.is_paused ? '▶️ 继续' : '⏸️ 暂停'}
            </button>
            <button 
              onClick={handleStop}
              style={{ ...controlBtnStyle, background: '#dc3545', color: '#fff' }}
            >
              ⏹️ 终止
            </button>
          </div>
        </>
      )}

      {(progress.status === 'completed' || progress.status === 'stopped') && (
        <button 
          onClick={handleReset}
          style={{ ...resetBtnStyle, background: colors.cardBg, border: `1px solid ${colors.border}`, color: colors.text }}
        >
          🔄 新建任务
        </button>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

const cardStyle: React.CSSProperties = {
  padding: '16px',
  borderRadius: '12px',
  border: '1px solid transparent',
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px 16px',
  borderRadius: '8px',
  outline: 'none',
  marginBottom: '8px',
  fontSize: '14px',
  fontFamily: 'inherit',
  lineHeight: '1.5',
};

const startBtnStyle: React.CSSProperties = {
  width: '100%',
  padding: '14px',
  background: '#0d6efd',
  color: '#fff',
  border: 'none',
  borderRadius: '8px',
  cursor: 'pointer',
  fontSize: '15px',
  fontWeight: 'bold',
  transition: 'all 0.2s',
};

const progressBarContainerStyle: React.CSSProperties = {
  height: '6px',
  borderRadius: '3px',
  overflow: 'hidden',
  background: 'rgba(128,128,128,0.2)',
};

const progressBarFillStyle: React.CSSProperties = {
  height: '100%',
  transition: 'width 0.3s ease',
};

const controlBtnStyle: React.CSSProperties = {
  flex: 1,
  padding: '14px',
  border: 'none',
  borderRadius: '8px',
  cursor: 'pointer',
  fontSize: '14px',
  fontWeight: 'bold',
};

const resetBtnStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px',
  borderRadius: '8px',
  cursor: 'pointer',
  fontSize: '14px',
  fontWeight: '600',
};
