import React, { useRef, useEffect, useState, useLayoutEffect } from 'react';
import { useAppStore } from '../stores/appStore';
import { apiClient } from '../api/client';

const levelColors: Record<string, string> = {
  DEBUG: '#6c757d',
  INFO: '#0dcaf0',
  WARNING: '#ffc107',
  ERROR: '#dc3545',
  CRITICAL: '#ff0000',
};

export const DebugPanel: React.FC = () => {
  const { logs, clearLogs, config } = useAppStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  
  const [snapshots, setSnapshots] = useState<string[]>([]);
  const [loadingSnapshots, setLoadingSnapshots] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'logs' | 'snapshots'>('logs');
  const [debugLogContent, setDebugLogContent] = useState('');
  const [loadingLog, setLoadingLog] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const contentRef = useRef('');
  const isAtBottomRef = useRef(true);

  const theme = config?.ui?.theme || 'dark';
  const colors = theme === 'light' ? {
    bg: '#f5f5f5',
    bgSecondary: '#fff',
    text: '#333',
    border: '#ddd',
    textSecondary: '#666',
    cardBg: '#fff',
    inputBg: '#fff',
  } : {
    bg: '#1e1e1e',
    bgSecondary: '#2d2d2d',
    text: '#fff',
    border: '#333',
    textSecondary: '#888',
    cardBg: '#2d2d2d',
    inputBg: '#1e1e1e',
  };

  useEffect(() => {
    if (activeTab === 'snapshots') {
      loadSnapshots();
    }
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === 'logs') {
      const loadDebugLog = async () => {
        setLoadingLog(true);
        try {
          const data = await apiClient.getDebugLog();
          if (data.exists && data.content !== contentRef.current) {
            contentRef.current = data.content;
            setDebugLogContent(data.content);
          }
        } catch (e) {
          console.error('Failed to load debug log:', e);
        } finally {
          setLoadingLog(false);
        }
      };
      loadDebugLog();
    }
  }, [activeTab]);

  useLayoutEffect(() => {
    if (debugLogContent && scrollRef.current && autoScroll) {
      const container = scrollRef.current;
      container.scrollTop = container.scrollHeight;
    }
  }, [debugLogContent, autoScroll]);

  const loadSnapshots = async () => {
    setLoadingSnapshots(true);
    try {
      const data = await apiClient.getSnapshots();
      setSnapshots(data.snapshots || []);
    } catch (e) {
      console.error('Failed to load snapshots:', e);
    } finally {
      setLoadingSnapshots(false);
    }
  };

  const handleSaveSnapshot = async () => {
    const name = `snapshot_${Date.now()}`;
    setSaving(true);
    try {
      await apiClient.saveSnapshot(name);
      await loadSnapshots();
    } catch (e) {
      console.error('Failed to save snapshot:', e);
    } finally {
      setSaving(false);
    }
  };

  const handleLoadSnapshot = async (name: string) => {
    try {
      const data = await apiClient.getSnapshot(name);
      if (data.status === 'success' && data.snapshot) {
        console.log('Snapshot loaded:', data.snapshot);
        alert(`快照 "${name}" 已加载`);
      } else {
        alert(`加载失败: ${data.message}`);
      }
    } catch (e) {
      console.error('Failed to load snapshot:', e);
    }
  };

  const handleDeleteSnapshot = async () => {
    alert('删除功能待实现：需要后端支持 DELETE /api/snapshot/{name}');
  };

  const btnStyle: React.CSSProperties = {
    padding: '6px 12px',
    borderRadius: '6px',
    border: `1px solid ${colors.border}`,
    background: colors.cardBg,
    color: colors.text,
    cursor: 'pointer',
    fontSize: '12px',
  };

  const tabBtnStyle: React.CSSProperties = {
    padding: '4px 10px',
    borderRadius: '4px',
    border: 'none',
    background: 'transparent',
    cursor: 'pointer',
    fontSize: '12px',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, color: colors.text }}>🔧 调试面板</h3>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={() => setActiveTab('logs')}
            style={{
              ...tabBtnStyle,
              background: activeTab === 'logs' ? colors.cardBg : 'transparent',
              color: activeTab === 'logs' ? '#0d6efd' : colors.textSecondary,
              border: `1px solid ${activeTab === 'logs' ? colors.border : 'transparent'}`,
            }}
          >
            📜 日志
          </button>
          <button 
            onClick={() => setActiveTab('snapshots')}
            style={{
              ...tabBtnStyle,
              background: activeTab === 'snapshots' ? colors.cardBg : 'transparent',
              color: activeTab === 'snapshots' ? '#0d6efd' : colors.textSecondary,
              border: `1px solid ${activeTab === 'snapshots' ? colors.border : 'transparent'}`,
            }}
          >
            💾 快照
          </button>
        </div>
      </div>

      {activeTab === 'logs' && (
        <>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={() => {
              const loadDebugLog = async () => {
                try {
                  const data = await apiClient.getDebugLog();
                  if (data.exists) {
                    setDebugLogContent(data.content);
                  }
                } catch (e) {
                  console.error('Failed to load debug log:', e);
                }
              };
              loadDebugLog();
            }} style={btnStyle}>🔄 刷新</button>
            <button 
              onClick={() => {
                setAutoScroll(!autoScroll);
                if (!autoScroll && scrollRef.current) {
                  scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
                }
              }} 
              style={{
                ...btnStyle,
                background: autoScroll ? '#198754' : colors.cardBg,
                color: autoScroll ? '#fff' : colors.text,
              }}
            >
              {autoScroll ? '🔃 自动滚动' : '⏸️ 暂停滚动'}
            </button>
          </div>
          
          <div style={{ 
            flex: 1, 
            overflow: 'auto', 
            background: colors.inputBg, 
            padding: '12px', 
            borderRadius: '8px',
            border: `1px solid ${colors.border}`,
            fontFamily: 'monospace',
            fontSize: '12px',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
            color: colors.text
          }} ref={scrollRef}>
            {loadingLog && <div style={{ color: colors.textSecondary }}>加载中...</div>}
            {!loadingLog && debugLogContent && (
              <div style={{ fontWeight: 'bold' }} dangerouslySetInnerHTML={{ 
                __html: debugLogContent
                  .replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;')
                  .split('\n').map((line, i) => {
                    let color = colors.text;
                    if (line.includes('ERROR') || line.includes('错误')) color = '#dc3545';
                    else if (line.includes('WARNING') || line.includes('警告')) color = '#ffc107';
                    else if (line.includes('INFO') || line.includes('信息')) color = '#0dcaf0';
                    else if (line.includes('DEBUG')) color = '#6c757d';
                    return `<div style="color:${color}">${line}</div>`;
                  }).join('')
              }} />
            )}
            {!loadingLog && !debugLogContent && (
              <div style={{ color: colors.textSecondary, textAlign: 'center', marginTop: '20px' }}>
                暂无日志内容<br/>
                <small>日志文件位于 logs/debug.log</small>
              </div>
            )}
          </div>
        </>
      )}

      {activeTab === 'snapshots' && (
        <>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button 
              onClick={handleSaveSnapshot} 
              disabled={saving}
              style={{ ...btnStyle, background: '#198754' }}
            >
              {saving ? '💾 保存中...' : '💾 保存快照'}
            </button>
            <button onClick={loadSnapshots} style={btnStyle}>🔄 刷新</button>
          </div>

          <div style={{ 
            flex: 1, 
            overflow: 'auto', 
            background: colors.inputBg, 
            padding: '12px', 
            borderRadius: '8px',
            border: `1px solid ${colors.border}`,
          }}>
            {loadingSnapshots ? (
              <div style={{ color: colors.textSecondary, textAlign: 'center' }}>加载中...</div>
            ) : snapshots.length === 0 ? (
              <div style={{ color: colors.textSecondary, textAlign: 'center' }}>暂无快照</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {snapshots.map((name) => (
                  <div key={name} style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    padding: '8px',
                    background: colors.cardBg,
                    borderRadius: '6px',
                    border: `1px solid ${colors.border}`,
                  }}>
                    <span style={{ color: colors.text, fontSize: '13px' }}>{name}</span>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button 
                        onClick={() => handleLoadSnapshot(name)}
                        style={{ ...btnStyle, padding: '4px 8px', fontSize: '11px' }}
                      >
                        加载
                      </button>
                      <button 
                        onClick={handleDeleteSnapshot}
                        style={{ ...btnStyle, padding: '4px 8px', fontSize: '11px', background: '#dc3545', color: '#fff', border: 'none' }}
                      >
                        删除
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
