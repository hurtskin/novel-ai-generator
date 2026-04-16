import React, { useState } from 'react';
import { useAppStore } from '../stores/appStore';
import { apiClient } from '../api/client';

export const InterventionPanel: React.FC = () => {
  const { interventionData, setSelectedPanel, config } = useAppStore();
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [confirming, setConfirming] = useState(false);

  const theme = config?.ui?.theme || 'dark';
  const colors = theme === 'light' ? {
    bg: '#f5f5f5',
    bgSecondary: '#fff',
    text: '#333',
    border: '#ddd',
    textSecondary: '#666',
    accent: '#0d6efd',
    success: '#198754',
    danger: '#dc3545',
  } : {
    bg: '#1e1e1e',
    bgSecondary: '#2d2d2d',
    text: '#fff',
    border: '#444',
    textSecondary: '#888',
    accent: '#0d6efd',
    success: '#198754',
    danger: '#dc3545',
  };

  const handleSelectVersion = (index: number) => {
    setSelectedVersion(index);
    setConfirming(true);
  };

  const handleConfirm = async () => {
    if (selectedVersion === null) return;
    try {
      await apiClient.selectVersion(selectedVersion);
      setSelectedPanel('progress');
    } catch (e) {
      console.error('Failed to select version:', e);
    }
  };

  const handleRetry = async () => {
    setConfirming(true);
    try {
      await apiClient.retryNode();
      setSelectedPanel('progress');
    } catch (e) {
      console.error('Failed to retry:', e);
    }
  };

  const handleCancel = () => {
    setSelectedVersion(null);
    setConfirming(false);
  };

  if (!interventionData) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100%',
        color: colors.text
      }}>
        <div>暂无人工介入请求</div>
        <button 
          onClick={() => setSelectedPanel('progress')}
          style={{
            marginTop: '20px',
            padding: '10px 20px',
            background: colors.accent,
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          返回进度页面
        </button>
      </div>
    );
  }

  const cardStyle: React.CSSProperties = {
    background: colors.bgSecondary,
    border: `1px solid ${colors.border}`,
    borderRadius: '8px',
    padding: '16px',
    marginBottom: '12px',
    maxHeight: '300px',
    overflow: 'auto',
  };

  const btnStyle: React.CSSProperties = {
    padding: '8px 16px',
    borderRadius: '6px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    marginRight: '8px',
  };

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%',
      background: colors.bg,
      color: colors.text,
      padding: '16px',
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '20px',
      }}>
        <h2 style={{ margin: 0 }}>⚠️ 人工介入</h2>
      </div>

      <div style={{ marginBottom: '16px', color: colors.textSecondary }}>
        <div>节点: <strong>{interventionData.nodeId}</strong></div>
        <div>章节: <strong>第 {interventionData.chapterId} 章</strong></div>
        <div>可用版本: <strong>{interventionData.versions.length}</strong> 个</div>
      </div>

      {!confirming ? (
        <>
          <div style={{ flex: 1, overflow: 'auto' }}>
            {interventionData.versions.map((content, index) => (
              <div key={index} style={cardStyle}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  marginBottom: '8px',
                }}>
                  <strong>版本 {index + 1}</strong>
                  <button
                    onClick={() => handleSelectVersion(index)}
                    style={{
                      ...btnStyle,
                      background: colors.accent,
                      color: '#fff',
                    }}
                  >
                    选择此版本
                  </button>
                </div>
                <pre style={{ 
                  margin: 0, 
                  whiteSpace: 'pre-wrap', 
                  wordBreak: 'break-all',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                }}>
                  {content}
                </pre>
              </div>
            ))}
          </div>

          <div style={{ 
            marginTop: '16px', 
            padding: '16px',
            background: colors.bgSecondary,
            borderRadius: '8px',
            border: `1px solid ${colors.border}`,
          }}>
            <div style={{ marginBottom: '12px', fontWeight: 'bold' }}>其他操作</div>
            <button
              onClick={handleRetry}
              style={{
                ...btnStyle,
                background: colors.danger,
                color: '#fff',
              }}
            >
              🔄 重试当前节点
            </button>
            <button
              onClick={() => setSelectedPanel('progress')}
              style={{
                ...btnStyle,
                background: colors.border,
                color: colors.text,
              }}
            >
              取消
            </button>
          </div>
        </>
      ) : (
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <div style={{ 
            marginBottom: '20px', 
            fontSize: '18px',
            textAlign: 'center',
          }}>
            {selectedVersion !== null ? (
              <>确定选择 <strong>版本 {selectedVersion + 1}</strong> 吗？</>
            ) : (
              <>确定 <strong>重试</strong> 当前节点吗？</>
            )}
          </div>
          <div>
            <button
              onClick={handleConfirm}
              style={{
                ...btnStyle,
                background: colors.success,
                color: '#fff',
                padding: '12px 24px',
                fontSize: '16px',
              }}
            >
              ✅ 确认
            </button>
            <button
              onClick={handleCancel}
              style={{
                ...btnStyle,
                background: colors.border,
                color: colors.text,
                padding: '12px 24px',
                fontSize: '16px',
              }}
            >
              返回
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
