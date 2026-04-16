# 滑动窗口审查系统

## 概述

将整章审查改为滑动窗口审查，每2个节点单元审查一次，大幅减少审查时间和重试成本。

## 触发条件

- 用户启动小说生成任务
- 每执行完2个角色扮演单元节点后

## 前置条件

1. 方案B流式检查已部署（llm_client.py 的 chat_with_completion_check）
2. 审查prompt已调整为窗口级别

## 执行流程

### 步骤1：初始化窗口状态

```python
# 数据结构
node_contents = {}  # {node_index: {"content": str, "versions": [str], "status": "pending"|"passed"}}
window_start = 0
window_size = 2
max_versions = 3
max_retries = 3
```

### 步骤2：执行窗口内节点

对于窗口 [window_start, window_start + window_size)：

1. 对每个节点执行 role_assigner + role_actor
2. 将生成内容存储到 node_contents[node_index]["versions"]
3. 累积到 chapter_content

### 步骤3：审查窗口内容

```python
# 审查输入
window_content = ""
for i in range(window_start, window_start + window_size):
    if i in node_contents:
        window_content += node_contents[i]["content"] + "\n"

# 前一个节点（用于衔接检查）
prev_content = ""
if window_start > 0 and window_start - 1 in node_contents:
    prev_content = node_contents[window_start - 1]["content"]
```

调用 self_check 函数：
- plan（导演标准）
- window_content（当前窗口内容）
- prev_content（前一个节点，用于衔接）
- global_memory（全局记忆）
- feedback（审查反馈）

### 步骤4：处理审查结果

**通过（needs_revision = false）：**
1. 清空 feedback
2. 将窗口内所有节点标记为 "passed"
3. 滑动窗口：window_start += window_size
4. 继续下一个窗口

**失败（needs_revision = true）：**
1. 记录审查反馈
2. 回退窗口：window_start = max(0, window_start - 1)
3. 重置窗口内节点状态为 "pending"
4. 继续当前窗口重试

### 步骤5：连续失败处理

```python
# 连续失败计数
consecutive_failures = 0
max_consecutive_failures = 3

if retry_count > max_retries:
    consecutive_failures += 1
    
if consecutive_failures >= max_consecutive_failures:
    # 暂停任务，推送版本列表到前端
    generation_state["is_paused"] = True
    generation_state["pending_versions"] = {
        "window_start": window_start,
        "nodes": []
    }
    for i in range(window_start, window_start + window_size):
        if i in node_contents:
            generation_state["pending_versions"]["nodes"].append({
                "index": i,
                "versions": node_contents[i]["versions"]
            })
    
    # 推送事件到前端
    await broadcast_ws("need_manual_review", {
        "window_start": window_start,
        "versions": generation_state["pending_versions"]
    })
```

### 步骤6：人工介入

前端显示版本列表，用户选择后：

```python
# API: POST /api/select_version
{
    "version_index": 1  # 选择第2个版本（从0开始）
}
```

后端处理：
1. 根据选择更新 node_contents
2. 清空 feedback
3. 继续滑动窗口

## API接口

### 获取版本列表

```
GET /api/versions/{window_start}

Response:
{
    "window_start": 0,
    "nodes": [
        {
            "index": 0,
            "versions": ["内容1", "内容2", "内容3"]
        },
        {
            "index": 1,
            "versions": ["内容1", "内容2"]
        }
    ]
}
```

### 提交版本选择

```
POST /api/select_version

Body:
{
    "version_index": 1
}

Response:
{
    "status": "version_selected",
    "version_index": 1
}
```

## 审查prompt调整

窗口级别审查需要调整输入：

```python
prompt = f"""作为质量审查专家，请检查以下内容的连贯性和一致性。

## 上一节内容（如有）
{prev_content}

## 当前窗口内容（{window_start} -{window_start + window_size}）
{window_content}

## 审查要点
1. 当前窗口内容与上一节内容的衔接是否自然
2. 角色行为是否一致
3. 情节发展是否合理
4. 情感转折是否流畅

## 输出格式
{{
    "needs_revision": true/false,
    "issue_types": [...],
    "specific_issues": [...],
    "improvement_suggestions": "..."
}}
"""
```

## 边界情况

1. **第一个窗口**：无 prev_content，仅审查内容本身
2. **最后一个窗口**：不足 window_size 个节点，只审查实际存在的节点
3. **单节点窗口**：第一个节点单独一个窗口

## 配置项

```yaml
generation:
  window_size: 2
  max_versions_per_node: 3
  max_retries: 3
  max_consecutive_failures: 3
```

## 注意事项

1. feedback 清空时机：每个窗口审查成功后立即清空
2. node_contents 持久化：需要保存到 generation_state
3. 版本列表限制：每个节点最多保存 max_versions_per_node 个版本
4. 全局记忆：保持使用，不精简导演标准
