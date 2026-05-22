import streamlit as st
import streamlit.components.v1 as components
import os
import base64
import json

# 页面基础配置
st.set_page_config(page_title="钧崽变变变", page_icon="🧩")
st.title("🧩 钧崽变变变")
st.subheader("🎮 游戏作者：魏菱延")
st.write("✅ 点击相邻方块移动 | 自动还原不计入榜单成绩")

# ===================== 服务器排行榜文件操作 =====================
RANK_FILE = "puzzle_rank.json"

def init_rank_file():
    if not os.path.exists(RANK_FILE):
        default_data = {"time_rank": [], "step_rank": []}
        with open(RANK_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

def load_rank():
    init_rank_file()
    with open(RANK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_score(time_sec: int, step: int):
    if time_sec <= 0 or step <= 0:
        return
    data = load_rank()
    data["time_rank"].append({"time": time_sec, "text": f"{time_sec//60:02d}:{time_sec%60:02d}"})
    data["step_rank"].append({"step": step})
    data["time_rank"] = sorted(data["time_rank"], key=lambda x: x["time"])[:5]
    data["step_rank"] = sorted(data["step_rank"], key=lambda x: x["step"])[:5]
    with open(RANK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clear_rank():
    init_rank_file()
    empty_data = {"time_rank": [], "step_rank": []}
    with open(RANK_FILE, "w", encoding="utf-8") as f:
        json.dump(empty_data, f, ensure_ascii=False, indent=2)

# ===================== 图片加载 =====================
image_files = [f for f in os.listdir('images') if f.endswith(('.jpg', '.jpeg', '.png'))]
image_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else 0)

image_base64_list = []
for img_file in image_files:
    try:
        with open(os.path.join('images', img_file), 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
            ext = img_file.split('.')[-1]
            mime = 'image/jpeg' if ext in ('jpg','jpeg') else 'image/png'
            image_base64_list.append(f'data:{mime};base64,{b64}')
    except Exception as e:
        st.error(f"图片加载失败：{e}")

if not image_base64_list:
    image_base64_list = ["https://picsum.photos/300"]
    image_files = ["默认图片.jpg"]

# ===================== 后端参数监听 =====================
init_rank_file()
rank_data = load_rank()
params = st.query_params

if "save" in params:
    try:
        t = int(params.get("time", 0))
        s = int(params.get("step", 0))
        save_score(t, s)
    except:
        pass
    st.query_params.clear()
    st.rerun()

if "clear" in params:
    clear_rank()
    st.query_params.clear()
    st.rerun()

# ===================== 前端页面与交互代码 =====================
puzzle_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:#f0f0f0;padding:10px;font-family: "Microsoft YaHei";}

    /* 按钮分成两行布局，解决遮挡问题 */
    .btn-row{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
        margin: 8px auto;
        flex-wrap: wrap;
        max-width: 400px;
    }
    button{
        padding: 8px 14px;
        border:none;
        border-radius:6px;
        background:#667eea;
        color:white;
        cursor:pointer;
        white-space: nowrap;
        font-size: 14px;
        user-select: none;
    }
    button:hover{background:#5568d3}
    select{
        padding:6px 8px;
        border-radius:6px;
        border:none;
        min-width:120px;
        font-size:14px;
    }

    .info{
        text-align:center;
        font-weight:bold;
        margin:10px 0;
        font-size:16px;
        color:#333;
    }

    .puzzle{max-width:320px;margin:10px auto}
    .grid{
        display:grid;
        grid-template-columns:repeat(3,1fr);
        gap:2px;
        background:#333;
        padding:2px;
        border-radius:8px;
        aspect-ratio:1;
    }
    .tile{
        background:#fff;
        background-size:300% 300%;
        border-radius:4px;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:24px;
        font-weight:bold;
        color:#fff;
        text-shadow:0 0 2px #000;
        cursor:pointer;
        /* 轻量化动画，减少卡顿 */
        transition: transform 0.08s ease;
        will-change: transform;
    }
    .tile.empty{background:#333!important;color:transparent}
    .tile.movable{box-shadow:0 0 5px #4ECDC4}

    /* 排行榜样式 */
    .rank-container{
        max-width: 320px;
        margin: 15px auto;
        display: flex;
        gap: 10px;
        justify-content: center;
    }
    .rank-box{
        background: white;
        padding: 10px;
        border-radius: 8px;
        width: 48%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .rank-title{
        text-align: center;
        font-weight: bold;
        color:#667eea;
        margin-bottom: 5px;
        font-size:14px;
    }
    .rank-item{
        font-size:12px;
        padding:3px 0;
        border-bottom:1px solid #f0f0f0;
        text-align: center;
    }
    .clear-btn{
        display:block;
        margin: 0 auto 10px;
        background:#ff6b6b;
    }
</style>
</head>
<body>
    <!-- 第一行按钮 -->
    <div class="btn-row">
        <button onclick="shufflePuzzle()">🔀 打乱</button>
        <button onclick="autoSolve()">🤖 自动还原</button>
    </div>
    <!-- 第二行切换图片按钮 -->
    <div class="btn-row">
        <button onclick="prevImage()">⬅️ 上一张</button>
        <button onclick="nextImage()">➡️ 下一张</button>
        <select id="imageSelect" onchange="selectImage(this.value)"></select>
    </div>

    <div class="info">步数：<span id="moves">0</span> &nbsp;&nbsp; 时长：<span id="time">00:00</span></div>
    <div class="puzzle"><div id="grid" class="grid"></div></div>

    <button class="clear-btn" onclick="clearRank()">清空排行榜</button>
    <div class="rank-container">
        <div class="rank-box">
            <div class="rank-title">🏆 最短时间</div>
            <div id="timeRank"></div>
        </div>
        <div class="rank-box">
            <div class="rank-title">🏆 最少步数</div>
            <div id="stepRank"></div>
        </div>
    </div>

<script>
const target = [1,2,3,4,5,6,7,8,0];
const dx = [-1,1,0,0];
const dy = [0,0,-1,1];

// 游戏变量
let board = [];
let squareImg = "";
let moves = 0;
let isSolving = false;
let currentImageIndex = 0;
const imageCache = {};
// 标记：区分手动游玩/自动还原，自动不计分
let manualPlay = true;

// 计时变量
let startTime = 0;
let timer = null;
let elapsedTime = 0;

// 后端传入排行榜数据
const SERVER_TIME_RANK = SERVER_TIME_RANK_PLACEHOLDER;
const SERVER_STEP_RANK = SERVER_STEP_RANK_PLACEHOLDER;

// 时间格式化
function formatTime(seconds) {
    const min = Math.floor(seconds / 60).toString().padStart(2, '0');
    const sec = (seconds % 60).toString().padStart(2, '0');
    return `${min}:${sec}`;
}

// 计时控制
function startTimer() {
    if (timer) clearInterval(timer);
    startTime = Date.now() - elapsedTime * 1000;
    timer = setInterval(() => {
        elapsedTime = Math.floor((Date.now() - startTime) / 1000);
        document.getElementById("time").textContent = formatTime(elapsedTime);
    }, 1000);
}
function stopTimer() { clearInterval(timer); timer = null; }
function resetTimer() {
    stopTimer();
    elapsedTime = 0;
    document.getElementById("time").textContent = formatTime(0);
}

// 图片缓存裁剪，预加载优化卡顿
async function cropSquare(url){
    if(imageCache[url]) return imageCache[url];
    return new Promise(res=>{
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.loading = "lazy";
        img.onload = ()=>{
            const size = Math.min(img.width, img.height);
            const canvas = document.createElement('canvas');
            canvas.width = canvas.height = size;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, (img.width-size)/2, (img.height-size)/2, size, size, 0,0,size,size);
            const data = canvas.toDataURL();
            imageCache[url] = data;
            res(data);
        };
        img.src = url;
    });
}

// 工具函数
const getEmptyIndex = () => board.findIndex(v => v === 0);
const isSolved = () => JSON.stringify(board) === JSON.stringify(target);

// 🔥深度优化：文档片段批量渲染，大幅减少DOM重绘卡顿
function render(){
    const grid = document.getElementById('grid');
    const emptyIdx = getEmptyIndex();
    const fragment = document.createDocumentFragment();
    grid.innerHTML = '';

    for(let i=0;i<9;i++){
        const tile = document.createElement('div');
        const val = board[i];
        if(val === 0){
            tile.className = 'tile empty';
        }else{
            tile.className = 'tile';
            tile.textContent = val;
            const idx = val - 1;
            const col = idx % 3;
            const row = Math.floor(idx / 3);
            tile.style.backgroundImage = `url(${squareImg})`;
            tile.style.backgroundPosition = `${col*50}% ${row*50}%`;

            const ex = Math.floor(emptyIdx/3), ey = emptyIdx%3;
            const ix = Math.floor(i/3), iy = i%3;
            if(Math.abs(ex-ix)+Math.abs(ey-iy)===1){
                tile.classList.add('movable');
                tile.onclick = () => move(i);
            }
        }
        fragment.appendChild(tile);
    }
    grid.appendChild(fragment);
    document.getElementById('moves').textContent = moves;

    // 仅手动游玩完成才提交成绩，自动还原不计分
    if(isSolved() && timer && manualPlay){
        stopTimer();
        submitScore();
    }
}

// 移动方块逻辑
function move(index){
    const emptyIdx = getEmptyIndex();
    [board[index], board[emptyIdx]] = [board[emptyIdx], board[index]];
    moves++;
    render();
}

// 图片选择初始化
function initImageSelect(){
    const select = document.getElementById('imageSelect');
    select.innerHTML = '';
    IMAGE_NAMES.forEach((name, idx) => {
        const option = document.createElement('option');
        option.value = idx;
        option.textContent = name.replace(/\.\w+$/, '');
        if(idx === currentImageIndex) option.selected = true;
        select.appendChild(option);
    });
}

// 切换图片，重置状态
async function selectImage(index){
    currentImageIndex = parseInt(index);
    board = [...target];
    moves = 0;
    resetTimer();
    isSolving = false;
    manualPlay = true;
    squareImg = await cropSquare(IMAGE_LIST[currentImageIndex]);
    render();
    // 切换图片后自动打乱，默认不显示完整原图
    autoShuffleBoard();
}
function prevImage(){
    currentImageIndex = (currentImageIndex - 1 + IMAGE_LIST.length) % IMAGE_LIST.length;
    selectImage(currentImageIndex);
}
function nextImage(){
    currentImageIndex = (currentImageIndex + 1) % IMAGE_LIST.length;
    selectImage(currentImageIndex);
}

// 内置打乱逻辑
function autoShuffleBoard(){
    for(let i=0;i<70;i++){
        const e = getEmptyIndex();
        const dirs = [-1,1,-3,3].filter(d=>{
            const n = e+d;
            if(n<0||n>=9) return false;
            if(e%3===0&&d===-1) return false;
            if(e%3===2&&d===1) return false;
            return true;
        });
        if(dirs.length){
            const r = dirs[Math.floor(Math.random()*dirs.length)];
            [board[e], board[e+r]] = [board[e+r], board[e]];
        }
    }
    render();
    startTimer();
}

// 手动打乱按钮
function shufflePuzzle(){
    moves = 0;
    resetTimer();
    manualPlay = true;
    autoShuffleBoard();
}

// 提交成绩到后端服务器文件
function submitScore() {
    if(elapsedTime <= 0 || moves <= 0) return;
    window.location.search = `save=1&time=${elapsedTime}&step=${moves}`;
}

// 清空排行榜
function clearRank() {
    window.location.search = `clear=1`;
}

// 渲染服务器榜单
function renderServerRank() {
    const timeDom = document.getElementById('timeRank');
    const stepDom = document.getElementById('stepRank');
    timeDom.innerHTML = SERVER_TIME_RANK.map((item, i) => 
        `<div class="rank-item">${i+1}. ${item.text}</div>`
    ).join('');
    stepDom.innerHTML = SERVER_STEP_RANK.map((item, i) => 
        `<div class="rank-item">${i+1}. ${item.step}步</div>`
    ).join('');
}

// 轻量化BFS自动还原，降低运算卡顿
async function autoSolve(){
    if(isSolved() || isSolving) return;
    isSolving = true;
    // 标记自动操作，不计入成绩
    manualPlay = false;

    const queue = [{state:[...board], space:getEmptyIndex(), steps:[]}];
    const visited = new Set([JSON.stringify(board)]);

    while(queue.length){
        const cur = queue.shift();
        if(JSON.stringify(cur.state) === JSON.stringify(target)){
            await executeSteps(cur.steps);
            isSolving = false;
            stopTimer();
            return;
        }
        const x = Math.floor(cur.space / 3);
        const y = cur.space % 3;
        for(let i=0;i<4;i++){
            const nx = x + dx[i], ny = y + dy[i];
            if(nx<0||nx>=3||ny<0||ny>=3) continue;
            const newSpace = nx*3+ny;
            const newState = [...cur.state];
            [newState[cur.space], newState[newSpace]] = [newState[newSpace], newState[cur.space]];
            const key = JSON.stringify(newState);
            if(!visited.has(key)){
                visited.add(key);
                queue.push({state:newState, space:newSpace, steps:[...cur.steps, newSpace]});
            }
        }
    }
    isSolving = false;
}

// 步骤执行，优化间隔更顺滑
async function executeSteps(steps){
    for(const pos of steps){
        move(pos);
        await new Promise(r => setTimeout(r, 120));
    }
}

// 页面初始化：开局默认打乱，不显示完整原图
const IMAGE_LIST = IMAGE_LIST_PLACEHOLDER;
const IMAGE_NAMES = IMAGE_NAMES_PLACEHOLDER;
async function init(){
    initImageSelect();
    renderServerRank();
    await selectImage(0);
}
init();
</script>
</body>
</html>
"""

# 数据占位符替换
image_list_str = '["' + '", "'.join(image_base64_list) + '"]'
image_names_str = '["' + '", "'.join(image_files) + '"]'
time_rank_str = json.dumps(rank_data["time_rank"], ensure_ascii=False)
step_rank_str = json.dumps(rank_data["step_rank"], ensure_ascii=False)

puzzle_html = puzzle_html.replace('IMAGE_LIST_PLACEHOLDER', image_list_str)
puzzle_html = puzzle_html.replace('IMAGE_NAMES_PLACEHOLDER', image_names_str)
puzzle_html = puzzle_html.replace('SERVER_TIME_RANK_PLACEHOLDER', time_rank_str)
puzzle_html = puzzle_html.replace('SERVER_STEP_RANK_PLACEHOLDER', step_rank_str)

components.html(puzzle_html, height=820)

st.write("---")
st.write("💡 规则：开局默认打乱状态 | 自动还原不计榜单成绩 | 手动闯关才可上榜")