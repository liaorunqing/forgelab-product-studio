# ForgeLab · AI Product Studio

一个面向玩具和消费产品创意的 AI 辅助生成工具：上传图片或视频，描述目标方向，自动提炼原型结构、功能、玩法与卖点，并生成“保留核心原理、改变外观或玩法”的产品方案。

## 效果预览

### 前端工作台

![ForgeLab 前端工作台](frontend-rounded-tested.png)

### 产品方案效果图

![产品方案效果图](generated-product.png)

## 核心能力

- 图片上传与视频关键帧提取
- AI 原型结构与功能分析
- 结构改款：保留硬件/内部结构，调整外观与配色
- 特性衍生：提取核心特性，生成不同产品方向
- 双方向生成：同时输出结构改款与特性衍生方案
- 产品文案、玩法、卖点、量产风险与效果图输出

## 本地运行

要求 Python 3.10+。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# 编辑 .env，填写火山方舟 API Key 和模型 Endpoint ID
python backend.py
```

打开 http://127.0.0.1:8000/。

## 配置说明

密钥只放在本地 `.env`，该文件已加入 `.gitignore`，不会提交到公开仓库。请参照 `.env.example` 配置文本模型、视觉模型和图片生成模型。

## 测试

```powershell
python -m py_compile backend.py
python test_file_button.py
```

## 许可证

本项目采用 [MIT License](LICENSE)。
