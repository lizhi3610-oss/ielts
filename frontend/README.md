# IELTS Speaking Coach - 启动指南

## 项目结构

```
ielts-speaking-coach-v0.1/
├── app/                    # 后端代码
│   ├── api/
│   │   ├── exam.py        # 考试接口
│   │   ├── practice.py    # 练习接口
│   │   └── questions.py   # 题库接口
│   ├── services/
│   │   ├── exam_service.py      # 考试业务逻辑
│   │   ├── practice_service.py  # 练习业务逻辑
│   │   └── question_service.py  # 题库业务逻辑
│   ├── models.py          # 数据库模型
│   ├── schemas.py         # 请求响应模型
│   └── main.py            # FastAPI 应用入口
├── frontend/              # 前端代码
│   ├── src/
│   │   ├── App.jsx        # 主组件
│   │   ├── App.css        # 样式文件
│   │   ├── api.js         # API 调用
│   │   └── main.jsx       # 入口文件
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── ielts.db               # SQLite 数据库
```

## 启动步骤

### 1. 启动后端服务

在项目根目录执行：

```bash
cd ~/Desktop/ielts-speaking-coach-v0.1
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

或在 PowerShell 中：

```powershell
cd ~\Desktop\ielts-speaking-coach-v0.1
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

后端服务启动后访问：
- **Swagger 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 2. 启动前端服务

打开新的终端窗口，执行：

```bash
cd ~/Desktop/ielts-speaking-coach-v0.1/frontend
npm install
npm run dev
```

或在 PowerShell 中：

```powershell
cd ~\Desktop\ielts-speaking-coach-v0.1\frontend
npm install
npm run dev
```

前端服务启动后访问：
- **前端页面**: http://localhost:5173

## 使用流程

1. 打开浏览器访问 http://localhost:5173
2. 点击"开始口语练习"按钮
3. 从题库中选择一道题目
4. 进入考试页面，查看考官问题
5. 在输入框中输入你的回答，点击"提交回答"
6. 系统会生成追问，继续回答（最多 3 轮）
7. 完成 3 轮对话后，点击"查看评分报告"
8. 查看模拟评分和反馈建议

## 技术栈

### 后端
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic

### 前端
- React 18
- Vite
- 原生 CSS

## 注意事项

1. 确保后端服务先启动，前端才能正常调用接口
2. 后端运行在 8000 端口，前端运行在 5173 端口
3. 已配置 CORS，允许前端跨域访问后端
4. 当前版本使用规则 Mock，未接入真实大模型
5. 评分为随机生成，仅供演示使用

## 常见问题

### 前端无法连接后端
- 检查后端服务是否启动
- 检查后端是否运行在 8000 端口
- 检查浏览器控制台是否有 CORS 错误

### npm install 失败
- 检查 Node.js 是否安装
- 尝试使用国内镜像：`npm install --registry=https://registry.npmmirror.com`

### 后端启动失败
- 检查虚拟环境是否激活
- 检查依赖是否安装：`pip install -r requirements.txt`
