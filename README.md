# 拼图游戏 🧩

一个基于 Streamlit 的在线拼图游戏，支持本地图片加载、计时和排行榜功能。

## 功能特点

- 🖼️ **本地图片支持**：自动加载 `images/` 目录下的图片
- ⏱️ **实时计时**：点击方块开始计时，记录完成时间
- 👣 **步数统计**：记录移动步数
- 🔄 **换图按钮**：切换不同图片进行游戏
- 🏆 **排行榜**：基于浏览器本地存储的排行榜（记录前10名）
- 🎉 **完成提示**：拼图完成后弹出庆祝窗口

## 本地运行

### 前置条件

- Python 3.8+
- uv（推荐）或 pip

### 安装依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 启动应用

```bash
# 使用 uv
uv run streamlit run app.py

# 或直接运行
streamlit run app.py
```

然后在浏览器中打开 `http://localhost:8501` 即可开始游戏。

## 部署到 Streamlit

1. 登录 Streamlit 官网：https://streamlit.io/
2. 点击 **Deploy an app**
3. 选择你的 GitHub 仓库
4. 配置：
   - Branch: `main`
   - Main file path: `app.py`
5. 点击 **Deploy**

## 项目结构

```
my_streamlit_app/
├── images/          # 存放拼图图片
│   ├── 1.jpg
│   ├── 2.jpg
│   ├── 3.jpg
│   ├── 4.jpg
│   └── 5.jpg
├── app.py           # Streamlit 主应用
├── main.py          # Kivy 版本（备用）
├── requirements.txt # 依赖列表
├── pyproject.toml   # uv 项目配置
└── README.md        # 项目说明
```

## 游戏玩法

1. 点击空格相邻的方块进行移动
2. 将所有方块恢复到正确位置即可完成
3. 完成后会自动记录成绩到排行榜

## 技术栈

- Streamlit - Web 应用框架
- Python - 后端逻辑
- HTML/CSS/JavaScript - 拼图游戏界面
- LocalStorage - 排行榜数据存储