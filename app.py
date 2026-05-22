import streamlit as st
import streamlit.components.v1 as components
import os
import base64

# 页面配置
st.set_page_config(page_title="钧崽变变变", page_icon="🧩")
st.title("🧩 钧崽变变变")
st.subheader("🎮 游戏作者：魏菱延")
st.write("✅ 点击空格相邻方块移动 | BFS最短路径自动还原")

# 读取图片（优化：仅加载一次）
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

# 无图片兼容
if not image_base64_list:
    image_base64_list = ["https://picsum.photos/300"]
    image_files = ["默认图片.jpg"]

# ====================== 核心HTML/JS代码 ======================
puzzle_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:#f0f0f0;padding:10px;font-family: "Microsoft YaHei";}
    
    /* -------- 🔥 修复按钮布局：整齐居中、不换行、无错乱 -------- */
    .control-group{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
        margin: 10px auto;
        flex-wrap: nowrap;
        max-width: 400px;
    }
    button{
        padding: 8px 12px;
        border:none;
        border-radius:6px;
        background:#667eea;
        color:white;
        cursor:pointer;
        white-space: nowrap;
        font-size: 14px;
    }
    button:hover{background:#5568d3}
    button.danger{background:#ff6b6b}
    select{
        padding:6px 8px;
        border-radius:6px;
        border:none;
        min-width:130px;
        font-size:14px;
    }

    /* 信息展示 */
    .info{
        text-align:center;
        font-weight:bold;
        margin:10px 0;
        font-size:16px;
        color:#333;
    }

    /* 拼图容器 */
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
        text-shadow:0 0 3px #000;
        cursor:pointer;
        transition: all 0.1s ease; /* 优化动画，减少卡顿 */
    }
    .tile.empty{background:#333!important;color:transparent}
    .tile.movable{box-shadow:0 0 6px #4ECDC4}

    /* -------- 🔥 新增排行榜样式 -------- */
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
    <!-- 整齐的控制按钮组 -->
    <div class="control-group">
        <button onclick="shufflePuzzle()">🔀 打乱</button>
        <button onclick="autoSolve()">🤖 自动还原</button>
        <button onclick="prevImage()">⬅️ 上一张</button>
        <button onclick="nextImage()">➡️ 下一张</button>
        <select id="imageSelect" onchange="selectImage(this.value)"></select>
    </div>

    <!-- 步数+时长展示 -->
    <div class="info">步数：<span id="moves">0</span> &nbsp;&nbsp; 时长：<span id="time">00:00</span></div>
    
    <!-- 拼图区域 -->
    <div class="puzzle"><div class="grid" id="grid"></div></div>

    <!-- 排行榜清空按钮 -->
    <button class="clear-btn" onclick="clearAllRank()">清空所有排行榜</button>
    <!-- 双排行榜 -->
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
// 基础配置
const N = 3;
const target = [1,2,3,4,5,6,7,8,0];
const dx = [-1,1,0,0];
const dy = [0,0,-1,1];

// 游戏核心变量
let board = [];
let squareImg = "";
let moves = 0;
let isSolving = false;
let currentImageIndex = 0;
let imageCache = {}; // 🔥 优化：图片缓存，避免重复裁剪

// 计时变量
let startTime = 0;
let timer = null;
let elapsedTime = 0;

// ====================== 🔥 性能优化：时间格式化 ======================
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

// ====================== 🔥 性能优化：图片缓存裁剪 ======================
async function cropSquare(url){
    if(imageCache[url]) return imageCache[url]; // 缓存命中，直接返回
    return new Promise(res=>{
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.onload = ()=>{
            const size = Math.min(img.width, img.height);
            const canvas = document.createElement('canvas');
            canvas.width = canvas.height = size;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, (img.width-size)/2, (img.height-size)/2, size, size, 0,0,size,size);
            const data = canvas.toDataURL();
            imageCache[url] = data; // 存入缓存
            res(data);
        };
        img.src = url;
    });
}

// 工具函数
function getEmptyIndex(){ return board.findIndex(v => v === 0); }
function isSolved(){ return JSON.stringify(board) === JSON.stringify(target); }

// ====================== 🔥 优化渲染：减少DOM重绘 ======================
function render(){
    const grid = document.getElementById('grid');
    const emptyIdx = getEmptyIndex();
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

            // 可移动判断
            const ex = Math.floor(emptyIdx/3), ey = emptyIdx%3;
            const ix = Math.floor(i/3), iy = i%3;
            if(Math.abs(ex-ix)+Math.abs(ey-iy)===1){
                tile.classList.add('movable');
                tile.onclick = () => move(i);
            }
        }
        grid.appendChild(tile);
    }
    document.getElementById('moves').textContent = moves;

    // 完成拼图：停止计时+保存排行榜
    if(isSolved() && timer){
        stopTimer();
        saveRank();
    }
}

// 移动方块
function move(index){
    const emptyIdx = getEmptyIndex();
    [board[index], board[emptyIdx]] = [board[emptyIdx], board[index]];
    moves++;
    render();
}

// 图片切换
function initImageSelect(){
    const select = document.getElementById('imageSelect');
    select.innerHTML = '';
    IMAGE_NAMES.forEach((name, idx) => {
        const option = document.createElement('option');
        option.value = idx;
        option.textContent = name.replace(/\.\w+$/, ''); // 隐藏后缀
        if(idx === currentImageIndex) option.selected = true;
        select.appendChild(option);
    });
}

async function selectImage(index){
    currentImageIndex = parseInt(index);
    board = [...target];
    moves = 0;
    resetTimer();
    isSolving = false;
    squareImg = await cropSquare(IMAGE_LIST[currentImageIndex]);
    render();
}
function prevImage(){
    currentImageIndex = (currentImageIndex - 1 + IMAGE_LIST.length) % IMAGE_LIST.length;
    selectImage(currentImageIndex);
}
function nextImage(){
    currentImageIndex = (currentImageIndex + 1) % IMAGE_LIST.length;
    selectImage(currentImageIndex);
}

// ====================== 🔥 修复BUG：打乱逻辑错误（原卡顿根源） ======================
function shufflePuzzle(){
    selectImage(currentImageIndex).then(()=>{
        for(let i=0;i<80;i++){ // 减少循环次数，优化性能
            const e = getEmptyIndex();
            const dirs = [-1,1,-3,3].filter(d=>{
                const n = e+d;
                if(n<0||n>=9) return false;
                if(e%3===0&&d===-1) return false;
                if(e%3===2&&d===1) return false; // 修复：e%2→e%3 致命逻辑错误
                return true;
            });
            if(dirs.length){
                const r = dirs[Math.floor(Math.random()*dirs.length)];
                [board[e], board[e+r]] = [board[e+r], board[e]];
            }
        }
        render();
        startTimer();
    });
}

// ====================== 🔥 新增：排行榜功能（本地存储，持久化保存） ======================
function saveRank() {
    if(elapsedTime === 0 || moves === 0) return;
    const timeRank = JSON.parse(localStorage.getItem('puzzle_time') || '[]');
    const stepRank = JSON.parse(localStorage.getItem('puzzle_step') || '[]');

    // 新增记录
    timeRank.push({ time: elapsedTime, str: formatTime(elapsedTime) });
    stepRank.push({ step: moves });

    // 排序+保留前5名
    timeRank.sort((a,b) => a.time - b.time).splice(5);
    stepRank.sort((a,b) => a.step - b.step).splice(5);

    // 保存
    localStorage.setItem('puzzle_time', JSON.stringify(timeRank));
    localStorage.setItem('puzzle_step', JSON.stringify(stepRank));

    // 刷新排行榜
    renderRank();
}

function renderRank() {
    const timeDom = document.getElementById('timeRank');
    const stepDom = document.getElementById('stepRank');
    const timeRank = JSON.parse(localStorage.getItem('puzzle_time') || '[]');
    const stepRank = JSON.parse(localStorage.getItem('puzzle_step') || '[]');

    // 渲染时间排行榜
    timeDom.innerHTML = timeRank.map((item, i) => 
        `<div class="rank-item">${i+1}. ${item.str}</div>`
    ).join('');

    // 渲染步数排行榜
    stepDom.innerHTML = stepRank.map((item, i) => 
        `<div class="rank-item">${i+1}. ${item.step}步</div>`
    ).join('');
}

// 清空排行榜
function clearAllRank() {
    localStorage.removeItem('puzzle_time');
    localStorage.removeItem('puzzle_step');
    renderRank();
    alert('排行榜已清空！');
}

// ====================== 🔥 优化BFS：更流畅的自动还原 ======================
async function autoSolve(){
    if(isSolved() || isSolving) return;
    isSolving = true;

    class Node { constructor(state, space, steps){
        this.state = state;
        this.space = space;
        this.steps = steps;
    }}

    const queue = [new Node([...board], getEmptyIndex(), [])];
    const visited = new Set([JSON.stringify(board)]);

    while(queue.length){
        const cur = queue.shift();
        if(JSON.stringify(cur.state) === JSON.stringify(target)){
            await executeSteps(cur.steps);
            isSolving = false;
            stopTimer();
            saveRank();
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
                queue.push(new Node(newState, newSpace, [...cur.steps, newSpace]));
            }
        }
    }
    isSolving = false;
}

// 优化步骤执行：减少延时，更流畅
async function executeSteps(steps){
    for(const pos of steps){
        move(pos);
        await new Promise(r => setTimeout(r, 150)); // 从200→150ms，更流畅
    }
}

// 初始化
const IMAGE_LIST = IMAGE_LIST_PLACEHOLDER;
const IMAGE_NAMES = IMAGE_NAMES_PLACEHOLDER;
async function init(){
    initImageSelect();
    renderRank(); // 初始化排行榜
    await selectImage(0);
}
init();
</script>
</body>
</html>
"""

# 注入数据
image_list_str = '["' + '", "'.join(image_base64_list) + '"]'
image_names_str = '["' + '", "'.join(image_files) + '"]'
puzzle_html = puzzle_html.replace('IMAGE_LIST_PLACEHOLDER', image_list_str)
puzzle_html = puzzle_html.replace('IMAGE_NAMES_PLACEHOLDER', image_names_str)

# 渲染页面
components.html(puzzle_html, height=850)

st.write("---")
st.write("💡 规则：点击与空格相邻的方块移动，还原拼图即可上榜！")