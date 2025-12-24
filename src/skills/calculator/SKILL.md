---
name: calculator
description: 计算数学表达式并获取当前时间，支持基本算术运算
---

# Calculator Skill

这个 skill 提供数学计算和时间查询能力。

## 何时使用

- 用户需要进行数学计算（加减乘除等）
- 用户需要查询当前时间
- 用户需要计算复杂的数学表达式

## 如何使用

### 计算数学表达式

使用 `calculator.py` 脚本进行计算：

```bash
python src/skills/calculator/calculator.py "2 + 2"
python src/skills/calculator/calculator.py "10 * 5 + 3"
python src/skills/calculator/calculator.py "(100 - 20) / 4"
```

**支持的运算符:**
- `+` 加法
- `-` 减法
- `*` 乘法
- `/` 除法
- `()` 括号

### 获取当前时间

```bash
python src/skills/calculator/calculator.py --time
```

## 示例

### 示例 1: 基本计算

**用户请求:** "帮我算一下 25 乘以 4 等于多少"

**方法:**
1. 识别这是一个数学计算任务
2. 执行: `python src/skills/calculator/calculator.py "25 * 4"`
3. 返回结果: 100

### 示例 2: 复杂表达式

**用户请求:** "计算 (100 + 50) / 3 的结果"

**方法:**
1. 识别这是一个带括号的表达式
2. 执行: `python src/skills/calculator/calculator.py "(100 + 50) / 3"`
3. 返回结果: 50.0

### 示例 3: 获取时间

**用户请求:** "现在几点了？"

**方法:**
1. 识别这是一个时间查询
2. 执行: `python src/skills/calculator/calculator.py --time`
3. 返回当前时间

## 注意事项

- 仅支持基本数学运算，不支持复杂函数如 sin、cos 等
- 表达式中不应包含变量或未定义的符号
- 除法结果可能为浮点数

