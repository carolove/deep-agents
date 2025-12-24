---
name: web-search
description: 使用 Tavily API 进行网络搜索，获取最新的网页信息和搜索结果
---

# Web Search Skill

这个 skill 提供网络搜索能力，使用 Tavily API 获取实时的网页搜索结果。

## 何时使用

- 用户需要搜索最新的信息
- 用户询问需要网络搜索才能回答的问题
- 需要获取某个主题的最新新闻或文章
- 需要查找特定网站或资源

## 前置条件

需要设置 `TAVILY_API_KEY` 环境变量：

```bash
export TAVILY_API_KEY="your-api-key"
```

如果未安装 tavily-python，需要先安装：

```bash
pip install tavily-python
```

## 如何使用

### 基本搜索

```bash
python src/skills/web-search/web_search.py "搜索查询"
```

### 限制结果数量

```bash
python src/skills/web-search/web_search.py "搜索查询" --max-results 5
```

## 输出格式

搜索结果包含：
- **标题**: 网页标题
- **URL**: 网页链接
- **摘要**: 网页内容摘要

每条结果格式如下：
```
1. [标题]
   URL: [链接]
   摘要: [内容摘要]
```

## 示例

### 示例 1: 搜索新闻

**用户请求:** "帮我搜索最新的人工智能新闻"

**方法:**
1. 识别这是一个网络搜索任务
2. 执行: `python src/skills/web-search/web_search.py "latest AI news"`
3. 返回搜索结果列表

### 示例 2: 技术查询

**用户请求:** "Python 3.12 有什么新特性？"

**方法:**
1. 识别需要搜索最新信息
2. 执行: `python src/skills/web-search/web_search.py "Python 3.12 new features" --max-results 5`
3. 总结搜索结果中的关键信息

### 示例 3: 产品信息

**用户请求:** "查找 MacBook Pro M3 的评测"

**方法:**
1. 构建搜索查询
2. 执行: `python src/skills/web-search/web_search.py "MacBook Pro M3 review"`
3. 整理并呈现评测信息

## 注意事项

- 需要有效的 TAVILY_API_KEY
- API 调用有速率限制，请合理使用
- 搜索结果可能因地区而异
- 建议使用英文关键词获取更好的结果

