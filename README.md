# IELTS Speaking Coach v0.5

文字版 IELTS Speaking 练习应用。

当前版本已经完成 Practice Mode 的文字对话闭环：选择 Part、选择 Topic、和考官多轮对话、结束后生成练习评价。Mock Exam 页面仍保留为后续完整考试流程入口。

## 当前功能

1. 首页入口：Practice Mode / Mock Exam / Records
2. Practice Mode 支持 Part 1 / Part 2 / Part 3
3. Practice Session 持久化：part、topic、status、started_at、finished_at、feedback_json
4. 每轮练习保存 examiner question 和 candidate answer
5. DeepSeek / OpenAI-compatible LLM 生成追问和评价
6. LLM 缺失或调用失败时自动 fallback，不让接口崩溃
7. Mock Exam 旧接口保留可用
8. 练习中可随时生成点评和推荐答案
9. 浏览器语音输入和考官问题朗读

## 技术栈

后端：

- FastAPI
- SQLAlchemy
- SQLite
- Pydantic

前端：

- React 18
- Vite
- 原生 CSS

## 环境准备

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

前端依赖：

```powershell
cd frontend
npm install
```

## 模型配置

复制 `.env.example` 为 `.env`：

```powershell
Copy-Item .env.example .env
```

填写 DeepSeek 配置：

```text
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

`.env` 不要提交到 Git。

## 启动

后端：

```powershell
cd C:\Users\wlz\Desktop\ielts-speaking-coach-v0.1
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

前端：

```powershell
cd C:\Users\wlz\Desktop\ielts-speaking-coach-v0.1\frontend
npm run dev -- --host 127.0.0.1
```

访问：

```text
http://127.0.0.1:5173
```

后端健康检查：

```text
http://127.0.0.1:8000/health
```

## 主要接口

```text
GET  /health
GET  /questions

POST /practice/sessions
POST /practice/sessions/{session_id}/answer
POST /practice/sessions/{session_id}/finish

POST /practice/submit
GET  /practice/records

POST /exam/start
POST /exam/answer
POST /exam/finish
```

## 测试

后端：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

前端：

```powershell
cd frontend
npm run build
```

## 部署

当前版本推荐先用 Render 部署一个 Docker Web Service。仓库里已经包含：

- `Dockerfile`：自动构建前端，并用 FastAPI 托管前端页面和后端接口。
- `render.yaml`：Render Blueprint 配置。

部署步骤：

1. 确认代码已经推送到 GitHub。
2. 在 Render 新建 Blueprint，选择本仓库。
3. 按页面提示填写 `DEEPSEEK_API_KEY`。
4. 部署完成后访问 Render 提供的公网地址。

当前免费部署使用 `/tmp/ielts.db` 作为 SQLite 数据库，适合演示和试用。服务器重启或重新部署后，历史练习记录可能丢失。正式长期使用时，建议改成 PostgreSQL 或付费持久化磁盘。

## 语音架构

当前语音 MVP 使用浏览器原生能力：

- 语音输入：Web Speech Recognition
- 考官朗读：Web Speech Synthesis
- Provider 入口：`frontend/src/speech/index.js`
- 交互流程：新问题自动朗读，用户手动开始语音回答，识别结果进入待提交文本，确认后手动提交
- 移动端：已接入临时识别结果和无声超时提示。Android Chrome/Edge 通常可用；如果 iPhone/Safari 不暴露语音识别能力，需要后续接入服务器端 ASR Provider。

后续接入 BosonAI 时，优先替换 speech provider，保留现有对话 UI 和练习流程。

## 下一阶段

v1 计划接入语音能力：

- 浏览器语音输入已完成第一版
- 考官问题朗读已完成第一版
- 后续可替换为 BosonAI ASR/TTS Provider
- 语音维度反馈
- 完整 Mock Exam 流程
