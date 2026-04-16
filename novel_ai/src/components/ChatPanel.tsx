import React, { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../stores/appStore';
import type { ChatMessage } from '../api/client';

export const ChatPanel: React.FC = () => {
  const { chatMessages, memories, currentRole, setCurrentRole, addChatMessage, updateChatMessage } = useAppStore();
  const [input, setInput] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const filteredMessages = currentRole === 'all' 
    ? chatMessages 
    : chatMessages.filter((m) => m.role === currentRole);

  const handleSend = () => {
    if (!input.trim()) return;
    const msg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };
    addChatMessage(msg);
    setInput('');
  };

  const handleRegenerate = (id: string) => {
    const msg = chatMessages.find((m) => m.id === id);
    if (msg) {
      setEditingId(id);
      setEditContent(msg.content);
    }
  };

  const handleSaveEdit = () => {
    if (editingId) {
      updateChatMessage(editingId, editContent);
      setEditingId(null);
      setEditContent('');
    }
  };

  return (
    <div style={{ display: 'flex', height: '100%', gap: '16px' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h3 style={{ margin: 0 }}>对话面板</h3>
          <select 
            value={currentRole} 
            onChange={(e) => setCurrentRole(e.target.value)}
            style={selectStyle}
          >
            <option value="all">全部</option>
            <option value="user">用户</option>
            <option value="assistant">AI</option>
            <option value="system">系统</option>
          </select>
        </div>

        <div ref={scrollRef} style={{ flex: 1, overflow: 'auto', marginBottom: '8px' }}>
          {filteredMessages.map((msg) => (
            <div key={msg.id} style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
              marginBottom: '12px'
            }}>
              <div style={{ 
                maxWidth: '80%', 
                padding: '8px 12px', 
                borderRadius: '8px',
                background: msg.role === 'user' ? '#0d6efd' : '#2d2d2d',
                color: '#fff',
                whiteSpace: 'pre-wrap'
              }}>
                {editingId === msg.id ? (
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    style={{ ...inputStyle, width: '100%', minHeight: '60px' }}
                  />
                ) : (
                  msg.content
                )}
              </div>
              <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                <span style={{ fontSize: '10px', color: '#666' }}>
                  {msg.timestamp.split('T')[1].split('.')[0]}
                </span>
                {msg.chapter !== undefined && (
                  <span style={{ fontSize: '10px', color: '#666' }}>
                    [C{msg.chapter}/N{msg.node}]
                  </span>
                )}
                {editingId === msg.id ? (
                  <button onClick={handleSaveEdit} style={smallBtnStyle}>保存</button>
                ) : (
                  <button onClick={() => handleRegenerate(msg.id)} style={smallBtnStyle}>编辑</button>
                )}
              </div>
            </div>
          ))}
          {filteredMessages.length === 0 && (
            <div style={{ color: '#666', textAlign: 'center', marginTop: '40px' }}>
              对话消息将在这里显示
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="输入消息..."
            style={{ ...inputStyle, flex: 1 }}
          />
          <button onClick={handleSend} style={btnStyle}>发送</button>
        </div>
      </div>

      <div style={{ width: '200px', borderLeft: '1px solid #333', paddingLeft: '16px' }}>
        <h4 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>记忆片段</h4>
        <div style={{ overflow: 'auto', maxHeight: 'calc(100% - 30px)' }}>
          {memories.map((mem) => (
            <div key={mem.id} style={{ 
              padding: '8px', 
              background: '#2d2d2d', 
              borderRadius: '4px', 
              marginBottom: '8px',
              fontSize: '12px'
            }}>
              <div style={{ color: '#0dcaf0', marginBottom: '4px' }}>
                [C{mem.chapter}/N{mem.node}]
              </div>
              <div style={{ color: '#ccc' }}>{mem.content.slice(0, 100)}...</div>
            </div>
          ))}
          {memories.length === 0 && <div style={{ color: '#666', fontSize: '12px' }}>无记忆片段</div>}
        </div>
      </div>
    </div>
  );
};

const btnStyle: React.CSSProperties = {
  padding: '8px 16px',
  background: '#0d6efd',
  color: '#fff',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
};

const smallBtnStyle: React.CSSProperties = {
  padding: '2px 8px',
  fontSize: '10px',
  background: '#444',
  color: '#fff',
  border: 'none',
  borderRadius: '2px',
  cursor: 'pointer',
};

const selectStyle: React.CSSProperties = {
  padding: '4px 8px',
  background: '#2d2d2d',
  color: '#fff',
  border: '1px solid #444',
  borderRadius: '4px',
};

const inputStyle: React.CSSProperties = {
  padding: '8px 12px',
  background: '#2d2d2d',
  color: '#fff',
  border: '1px solid #444',
  borderRadius: '4px',
  outline: 'none',
};
