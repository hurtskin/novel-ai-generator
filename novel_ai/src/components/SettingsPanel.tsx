import React, { useState, useEffect } from 'react';
import { useAppStore } from '../stores/appStore';
import { apiClient } from '../api/client';

const MODELS = [
  { value: 'moonshot-v1-128k', label: 'moonshot-v1-128k' },
  { value: 'moonshot-v1-8k-vision-preview', label: 'moonshot-v1-8k-vision-preview' },
  { value: 'moonshot-v1-8k', label: 'moonshot-v1-8k' },
  { value: 'moonshot-v1-32k', label: 'moonshot-v1-32k' },
  { value: 'kimi-k2.5', label: 'kimi-k2.5 (推荐)' },
  { value: 'kimi-k2-thinking-turbo', label: 'kimi-k2-thinking-turbo' },
  { value: 'kimi-k2-0905-preview', label: 'kimi-k2-0905-preview' },
];

const GENRES = [
  { value: 'novel', label: '小说 (Novel)' },
  { value: 'script', label: '剧本 (Script)' },
  { value: 'game_story', label: '游戏剧情 (Game Story)' },
  { value: 'dialogue', label: '对话 (Dialogue)' },
  { value: 'article', label: '文章 (Article)' },
];

const LANGUAGES = [
  { value: 'zh-CN', label: '中文' },
  { value: 'en', label: 'English' },
];

const THEMES = [
  { value: 'dark', label: '深色 (Dark)' },
  { value: 'light', label: '浅色 (Light)' },
];

export const SettingsPanel: React.FC = () => {
  const { config, setConfig, setError } = useAppStore();
  const [localConfig, setLocalConfig] = useState<typeof config>(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const theme = config?.ui?.theme || 'dark';
  const colors = theme === 'light' ? {
    bg: '#f5f5f5',
    bgSecondary: '#fff',
    text: '#333',
    border: '#ddd',
    textSecondary: '#666',
    inputBg: '#fff',
    accent: '#0d6efd',
    accentText: '#0dcaf0',
  } : {
    bg: '#1e1e1e',
    bgSecondary: '#2d2d2d',
    text: '#fff',
    border: '#444',
    textSecondary: '#888',
    inputBg: '#1e1e1e',
    accent: '#0d6efd',
    accentText: '#0dcaf0',
  };

  const containerStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    background: colors.bg,
  };

  const sectionStyle: React.CSSProperties = {
    background: colors.bgSecondary,
    padding: '20px',
    borderRadius: '12px',
    marginBottom: '16px',
    border: `1px solid ${colors.border}`,
  };

  const sectionTitleStyle: React.CSSProperties = {
    margin: '0 0 16px 0',
    fontSize: '16px',
    color: colors.accentText,
    borderBottom: `1px solid ${colors.border}`,
    paddingBottom: '8px',
  };

  const fieldGroupStyle: React.CSSProperties = {
    marginBottom: '16px',
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    marginBottom: '6px',
    fontSize: '13px',
    color: colors.textSecondary,
  };

  const inputGroupStyle: React.CSSProperties = {
    display: 'flex',
    gap: '8px',
  };

  const toggleBtnStyle: React.CSSProperties = {
    padding: '8px 12px',
    background: colors.border,
    color: colors.text,
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
  };

  const rowStyle: React.CSSProperties = {
    display: 'flex',
    gap: '16px',
  };

  const sliderLabelStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '8px',
  };

  const valueStyle: React.CSSProperties = {
    color: colors.accentText,
    fontWeight: 600,
  };

  const sliderHintStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '11px',
    color: colors.textSecondary,
    marginTop: '4px',
  };

  const rangeStyle: React.CSSProperties = {
    width: '100%',
    height: '6px',
    borderRadius: '3px',
    background: colors.inputBg,
    outline: 'none',
    cursor: 'pointer',
    appearance: 'none',
  };

  const hintStyle: React.CSSProperties = {
    display: 'block',
    marginTop: '6px',
    fontSize: '12px',
    color: colors.textSecondary,
  };

  const loadingStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    gap: '16px',
    color: colors.textSecondary,
  };

  const spinnerStyle: React.CSSProperties = {
    width: '32px',
    height: '32px',
    border: `3px solid ${colors.border}`,
    borderTopColor: colors.accent,
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
    flexShrink: 0,
  };

  const titleStyle: React.CSSProperties = {
    margin: 0,
    fontSize: '20px',
    color: colors.text,
  };

  const headerButtonsStyle: React.CSSProperties = {
    display: 'flex',
    gap: '8px',
  };

  const saveBtnStyle: React.CSSProperties = {
    padding: '8px 20px',
    background: colors.accent,
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 600,
    transition: 'all 0.2s',
  };

  const saveBtnSuccessStyle: React.CSSProperties = {
    ...saveBtnStyle,
    background: '#198754',
  };

  const resetBtnStyle: React.CSSProperties = {
    ...saveBtnStyle,
    background: '#6c757d',
  };

  const toggleSwitchStyle: React.CSSProperties = {
    position: 'relative',
    display: 'inline-block',
    width: '52px',
    height: '28px',
  };

  const checkboxStyle: React.CSSProperties = {
    opacity: 0,
    width: 0,
    height: 0,
  };

  const toggleSliderStyle: React.CSSProperties = {
    position: 'absolute',
    cursor: 'pointer',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: colors.border,
    transition: '0.3s',
    borderRadius: '28px',
  };

  const toggleKnobStyle: React.CSSProperties = {
    position: 'absolute',
    content: '""',
    height: '22px',
    width: '22px',
    left: '3px',
    bottom: '3px',
    backgroundColor: '#fff',
    transition: '0.3s',
    borderRadius: '50%',
  };

  const prefixStyle: React.CSSProperties = {
    position: 'absolute',
    left: '12px',
    top: '50%',
    transform: 'translateY(-50%)',
    color: colors.textSecondary,
    fontSize: '14px',
  };

  const scrollContainerStyle: React.CSSProperties = {
    flex: 1,
    overflow: 'auto',
    paddingRight: '8px',
  };

  const selectStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 12px',
    background: colors.inputBg,
    color: colors.text,
    border: `1px solid ${colors.border}`,
    borderRadius: '6px',
    fontSize: '14px',
    outline: 'none',
    cursor: 'pointer',
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 12px',
    background: colors.inputBg,
    color: colors.text,
    border: `1px solid ${colors.border}`,
    borderRadius: '6px',
    fontSize: '14px',
    outline: 'none',
    transition: 'border-color 0.2s',
  };

  useEffect(() => {
    const loadConfig = async () => {
      if (!config) {
        try {
          const cfg = await apiClient.getConfig();
          setConfig(cfg);
        } catch (e) {
          console.error('Failed to load config:', e);
        }
      } else {
        const configWithDefaults = {
          ...config,
          ollama: config.ollama || {
            enabled: false,
            base_url: 'http://localhost:11434',
            model: 'qwen2.5:7b',
            timeout: 120
          },
          api: {
            ...config.api,
            provider: config.api?.provider || 'api'
          }
        };
        setLocalConfig(configWithDefaults);
      }
    };
    loadConfig();
  }, [config]);

  const handleSave = async () => {
    if (!localConfig) return;
    setSaving(true);
    setSaved(false);
    try {
      await apiClient.saveConfig(localConfig);
      setConfig(localConfig);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      setError('保存配置失败: ' + (e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (config) {
      setLocalConfig({ ...config });
    }
  };

  if (!localConfig) {
    return (
      <div style={loadingStyle}>
        <div style={spinnerStyle} />
        <div>加载配置中...</div>
      </div>
    );
  }

  const updateApi = (field: string, value: any) => {
    setLocalConfig({
      ...localConfig,
      api: { ...localConfig.api, [field]: value }
    });
  };

  const updateGeneration = (field: string, value: any) => {
    setLocalConfig({
      ...localConfig,
      generation: { ...localConfig.generation, [field]: value }
    });
  };

  const updateUi = (field: string, value: any) => {
    setLocalConfig({
      ...localConfig,
      ui: { ...localConfig.ui, [field]: value }
    });
  };

  const updatePerformance = (field: string, value: any) => {
    setLocalConfig({
      ...localConfig,
      performance: { ...localConfig.performance, [field]: value }
    });
  };

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <h2 style={titleStyle}>⚙️ 设置</h2>
        <div style={headerButtonsStyle}>
          <button onClick={handleReset} style={resetBtnStyle} disabled={saving}>
            重置
          </button>
          <button onClick={handleSave} style={saved ? saveBtnSuccessStyle : saveBtnStyle} disabled={saving}>
            {saving ? '保存中...' : saved ? '✓ 已保存' : '保存配置'}
          </button>
        </div>
      </div>

      <div style={scrollContainerStyle}>
        <section style={sectionStyle}>
          <h3 style={sectionTitleStyle}>🔌 LLM 提供商</h3>
          
          <div style={fieldGroupStyle}>
            <label style={labelStyle}>Provider (LLM 提供商)</label>
            <select
              value={localConfig.api.provider || 'api'}
              onChange={(e) => updateApi('provider', e.target.value)}
              style={selectStyle}
            >
              <option value="api">Kimi API</option>
              <option value="ollama">Ollama (本地模型)</option>
            </select>
            <div style={hintStyle}>
              {localConfig.api.provider === 'ollama' 
                ? '使用本地 Ollama 模型运行，将忽略下方 API 配置' 
                : '使用 Kimi 云端 API 调用'}
            </div>
          </div>
        </section>

        {localConfig.api.provider !== 'ollama' && (
          <section style={sectionStyle}>
            <h3 style={sectionTitleStyle}>☁️ Kimi API 配置</h3>
            
            <div style={fieldGroupStyle}>
              <label style={labelStyle}>API Key (Kimi 密钥)</label>
              <div style={inputGroupStyle}>
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={localConfig.api.api_key}
                  onChange={(e) => updateApi('api_key', e.target.value)}
                  style={inputStyle}
                  placeholder="sk-..."
                />
                <button onClick={() => setShowApiKey(!showApiKey)} style={toggleBtnStyle}>
                  {showApiKey ? '🔒' : '👁️'}
                </button>
              </div>
            </div>

            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Base URL (API 地址)</label>
              <input
                type="text"
                value={localConfig.api.base_url}
                onChange={(e) => updateApi('base_url', e.target.value)}
                style={inputStyle}
                placeholder="https://api.moonshot.cn/v1"
              />
            </div>

            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Model (模型)</label>
              <select
                value={localConfig.api.model}
                onChange={(e) => updateApi('model', e.target.value)}
                style={selectStyle}
              >
                {MODELS.map(m => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>

            <div style={rowStyle}>
              <div style={{ ...fieldGroupStyle, flex: 1 }}>
                <label style={labelStyle}>Timeout (超时秒数)</label>
                <input
                  type="number"
                  min="10"
                  max="300"
                  value={localConfig.api.timeout}
                  onChange={(e) => updateApi('timeout', parseInt(e.target.value))}
                  style={inputStyle}
                />
              </div>
              <div style={{ ...fieldGroupStyle, flex: 1 }}>
                <label style={labelStyle}>Max Retries (最大重试)</label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={localConfig.api.max_retries}
                  onChange={(e) => updateApi('max_retries', parseInt(e.target.value))}
                  style={inputStyle}
                />
              </div>
            </div>
          </section>
        )}

        {localConfig.api.provider === 'ollama' && localConfig.ollama && (
          <section style={sectionStyle}>
            <h3 style={sectionTitleStyle}>🦙 Ollama 本地模型</h3>
            
            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Enable (启用)</label>
              <label style={toggleSwitchStyle}>
                <input
                  type="checkbox"
                  checked={localConfig.ollama.enabled}
                  onChange={(e) => setLocalConfig({
                    ...localConfig,
                    ollama: { ...localConfig.ollama!, enabled: e.target.checked }
                  })}
                  style={checkboxStyle}
                />
                <span style={{
                  ...toggleSliderStyle,
                  backgroundColor: localConfig.ollama.enabled ? '#4CAF50' : '#ccc',
                }}>
                  <span style={{
                    ...toggleKnobStyle,
                    transform: localConfig.ollama.enabled ? 'translateX(24px)' : 'translateX(0)',
                  }} />
                </span>
              </label>
            </div>

            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Base URL (服务地址)</label>
              <input
                type="text"
                value={localConfig.ollama.base_url}
                onChange={(e) => setLocalConfig({
                  ...localConfig,
                  ollama: { ...localConfig.ollama!, base_url: e.target.value }
                })}
                style={inputStyle}
                placeholder="http://localhost:11434"
              />
            </div>

            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Model (模型名称)</label>
              <input
                type="text"
                value={localConfig.ollama.model}
                onChange={(e) => setLocalConfig({
                  ...localConfig,
                  ollama: { ...localConfig.ollama!, model: e.target.value }
                })}
                style={inputStyle}
                placeholder="qwen2.5:7b"
              />
            </div>

            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Timeout (超时秒数)</label>
              <input
                type="number"
                min="10"
                max="600"
                value={localConfig.ollama.timeout}
                onChange={(e) => setLocalConfig({
                  ...localConfig,
                  ollama: { ...localConfig.ollama!, timeout: parseInt(e.target.value) }
                })}
                style={inputStyle}
              />
            </div>
          </section>
        )}

        <section style={sectionStyle}>
          <h3 style={sectionTitleStyle}>🎨 生成参数</h3>
          
          <div style={fieldGroupStyle}>
            <div style={sliderLabelStyle}>
              <span>Temperature (随机性)</span>
              <span style={valueStyle}>{localConfig.generation.temperature}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={localConfig.generation.temperature}
              onChange={(e) => updateGeneration('temperature', parseFloat(e.target.value))}
              style={rangeStyle}
            />
            <div style={sliderHintStyle}>
              <span>精确</span>
              <span>随机</span>
            </div>
          </div>

          <div style={fieldGroupStyle}>
            <div style={sliderLabelStyle}>
              <span>Top P (核采样)</span>
              <span style={valueStyle}>{localConfig.generation.top_p}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={localConfig.generation.top_p}
              onChange={(e) => updateGeneration('top_p', parseFloat(e.target.value))}
              style={rangeStyle}
            />
            <div style={sliderHintStyle}>
              <span>集中</span>
              <span>多样</span>
            </div>
          </div>

          <div style={fieldGroupStyle}>
            <label style={labelStyle}>Max Tokens (最大生成Token)</label>
            <input
              type="number"
              min="100"
              max="64000"
              step="100"
              value={localConfig.generation.max_tokens}
              onChange={(e) => updateGeneration('max_tokens', parseInt(e.target.value))}
              style={inputStyle}
            />
          </div>
        </section>

        <section style={sectionStyle}>
          <h3 style={sectionTitleStyle}>🖥️ 界面设置</h3>
          
          <div style={rowStyle}>
            <div style={{ ...fieldGroupStyle, flex: 1 }}>
              <label style={labelStyle}>Theme (主题)</label>
              <select
                value={localConfig.ui.theme}
                onChange={(e) => updateUi('theme', e.target.value)}
                style={selectStyle}
              >
                {THEMES.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div style={{ ...fieldGroupStyle, flex: 1 }}>
              <label style={labelStyle}>Language (语言)</label>
              <select
                value={localConfig.ui.language}
                onChange={(e) => updateUi('language', e.target.value)}
                style={selectStyle}
              >
                {LANGUAGES.map(l => (
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={fieldGroupStyle}>
            <div style={sliderLabelStyle}>
              <span>Font Size (字号)</span>
              <span style={valueStyle}>{localConfig.ui.font_size}px</span>
            </div>
            <input
              type="range"
              min="12"
              max="20"
              step="1"
              value={localConfig.ui.font_size}
              onChange={(e) => updateUi('font_size', parseInt(e.target.value))}
              style={rangeStyle}
            />
          </div>

          <div style={fieldGroupStyle}>
            <label style={labelStyle}>Font Family (字体)</label>
            <input
              type="text"
              value={localConfig.ui.font_family}
              onChange={(e) => updateUi('font_family', e.target.value)}
              style={inputStyle}
              placeholder="system-ui, -apple-system, sans-serif"
            />
          </div>
        </section>

        <section style={sectionStyle}>
          <h3 style={sectionTitleStyle}>⚡ 性能阈值</h3>
          
          <div style={fieldGroupStyle}>
            <label style={labelStyle}>Cost Alert USD (成本告警线)</label>
            <div style={inputGroupStyle}>
              <span style={prefixStyle}>$</span>
              <input
                type="number"
                min="0.1"
                max="100"
                step="0.1"
                value={localConfig.performance.cost_alert_usd}
                onChange={(e) => updatePerformance('cost_alert_usd', parseFloat(e.target.value))}
                style={{ ...inputStyle, paddingLeft: '24px' }}
              />
            </div>
            <div style={hintStyle}>当预估成本超过此值时界面会显示红色警告</div>
          </div>
        </section>

        <section style={sectionStyle}>
          <h3 style={sectionTitleStyle}>📖 文体选择</h3>
          
          <div style={fieldGroupStyle}>
            <label style={labelStyle}>Genre (生成文体)</label>
            <select
              value={localConfig.genre}
              onChange={(e) => setLocalConfig({ ...localConfig, genre: e.target.value as any })}
              style={selectStyle}
            >
              {GENRES.map(g => (
                <option key={g.value} value={g.value}>{g.label}</option>
              ))}
            </select>
            <div style={hintStyle}>
              {localConfig.genre === 'novel' && '长篇小说，章节结构，角色弧光'}
              {localConfig.genre === 'script' && '剧本，场景-镜头-对白格式'}
              {localConfig.genre === 'game_story' && '游戏剧情，分支选择，状态机'}
              {localConfig.genre === 'dialogue' && '多轮对话，角色扮演，记忆累积'}
              {localConfig.genre === 'article' && '长文章，论点-论据-结论结构'}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};
