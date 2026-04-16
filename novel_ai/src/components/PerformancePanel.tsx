import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { useAppStore } from '../stores/appStore';

export const PerformancePanel: React.FC = () => {
  const { nodeMetrics, chapterMetrics, totalMetrics, config } = useAppStore();

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

  const latestMetric = nodeMetrics[nodeMetrics.length - 1];
  const tps = latestMetric?.tps || 0;
  const cost = totalMetrics?.total_cost_usd || 0;

  const chartData = chapterMetrics.map((ch) => ({
    chapter: `C${ch.chapter_id}`,
    tokens: ch.total_tokens,
    cost: ch.total_cost_usd,
  }));

  const latencyData = nodeMetrics.map((n, i) => ({
    index: i + 1,
    latency_ms: n.ttf_ms || 0,
  }));

  const exportReport = () => {
    const report = `# 性能测试报告
生成时间: ${new Date().toISOString()}

## 总体指标
- 总章节数: ${totalMetrics?.total_chapters || 0}
- 总耗时: ${totalMetrics?.total_duration_min?.toFixed(2) || 0} 分钟
- 总 Token: ${totalMetrics?.total_tokens || 0}
- 总成本: $${totalMetrics?.total_cost_usd?.toFixed(4) || 0}

## 每章详情
${chapterMetrics.map(ch => `- 章节 ${ch.chapter_id}: ${ch.total_tokens} tokens, $${ch.total_cost_usd.toFixed(4)}, ${(ch.total_duration_ms / 1000 / 60).toFixed(2)} 分钟`).join('\n')}

## 节点详情
${nodeMetrics.map(n => `- ${n.node_id}: ${n.total_tokens} tokens, ${n.tps.toFixed(2)} t/s, $${n.cost_usd.toFixed(4)}`).join('\n')}
`;
    const blob = new Blob([report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `performance_report_${Date.now()}.md`;
    a.click();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, color: colors.text }}>⚡ 性能面板</h3>
        <button onClick={exportReport} style={btnStyle}>📊 导出报告</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div style={{ ...cardStyle, background: colors.cardBg, border: `1px solid ${colors.border}` }}>
          <div style={{ fontSize: '12px', color: colors.textSecondary }}>生成速度</div>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#0dcaf0' }}>
            {tps.toFixed(2)} <span style={{ fontSize: '14px' }}>tokens/s</span>
          </div>
        </div>

        <div style={{ ...cardStyle, background: colors.cardBg, border: `1px solid ${colors.border}` }}>
          <div style={{ fontSize: '12px', color: colors.textSecondary }}>预估成本</div>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: cost > 5 ? '#dc3545' : '#198754' }}>
            ${cost.toFixed(4)}
          </div>
        </div>
      </div>

      <div style={{ flex: 1, minHeight: '180px' }}>
        <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: colors.text }}>📊 Token 消耗（按章节）</h4>
        <ResponsiveContainer width="100%" height={150}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
            <XAxis dataKey="chapter" stroke={colors.textSecondary} fontSize={12} />
            <YAxis stroke={colors.textSecondary} fontSize={12} />
            <Tooltip 
              contentStyle={{ background: colors.cardBg, border: `1px solid ${colors.border}`, color: colors.text }}
              labelStyle={{ color: colors.text }}
            />
            <Bar dataKey="tokens" fill={colors.accent} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {latencyData.length > 0 && (
        <div style={{ flex: 1, minHeight: '180px' }}>
          <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: colors.text }}>⏱️ 首 Token 延迟（按节点）</h4>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={latencyData}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
              <XAxis dataKey="index" stroke={colors.textSecondary} fontSize={12} />
              <YAxis stroke={colors.textSecondary} fontSize={12} />
              <Tooltip 
                contentStyle={{ background: colors.cardBg, border: `1px solid ${colors.border}`, color: colors.text }}
                labelStyle={{ color: colors.text }}
              />
              <Line type="monotone" dataKey="latency_ms" stroke="#ffc107" strokeWidth={2} dot={{ fill: '#ffc107' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {nodeMetrics.length > 0 && (
        <div style={{ ...cardStyle, background: colors.cardBg, border: `1px solid ${colors.border}` }}>
          <div style={{ fontSize: '13px', color: colors.textSecondary }}>
            📍 节点数: <span style={{ color: colors.text, fontWeight: 600 }}>{nodeMetrics.length}</span> | 
            📝 总Token: <span style={{ color: colors.text, fontWeight: 600 }}>{nodeMetrics.reduce((a, b) => a + b.total_tokens, 0).toLocaleString()}</span> | 
            💰 总成本: <span style={{ color: '#198754', fontWeight: 600 }}>${nodeMetrics.reduce((a, b) => a + b.cost_usd, 0).toFixed(4)}</span>
          </div>
        </div>
      )}
    </div>
  );
};

const btnStyle: React.CSSProperties = {
  padding: '8px 16px',
  background: '#0d6efd',
  color: '#fff',
  border: 'none',
  borderRadius: '6px',
  cursor: 'pointer',
  fontSize: '13px',
  fontWeight: 500,
};

const cardStyle: React.CSSProperties = {
  padding: '16px',
  borderRadius: '8px',
};
