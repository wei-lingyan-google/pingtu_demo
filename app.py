import streamlit as st
import streamlit.components.v1 as components
import os
import base64
import json
from PIL import Image
import io

# 页面基础配置
st.set_page_config(page_title="钧崽变变变", page_icon="🧩")
st.title("🧩 钧崽变变变")
st.subheader("🎮 游戏作者：魏菱延")
st.write("✅ 点击相邻方块移动 | 自动还原不计入榜单成绩")

# ===================== 服务器排行榜文件操作 =====================
RANK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "puzzle_rank.json")

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
    # 去重处理
    time_exists = any(item["time"] == time_sec for item in data["time_rank"])
    step_exists = any(item["step"] == step for item in data["step_rank"])
    if not time_exists:
        data["time_rank"].append({"time": time_sec, "text": f"{time_sec//60:02d}:{time_sec%60:02d}"})
    if not step_exists:
        data["step_rank"].append({"step": step})
    # 排序并截取前5名
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

# 兜底图片，防止黑屏
if not image_base64_list:
    img = Image.new('RGB', (300, 300), color=(102, 126, 234))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    image_base64_list = [f'data:image/jpeg;base64,{b64}']
    image_files = ["默认图片.jpg"]

# ===================== 后端参数监听（修复执行顺序） =====================
init_rank_file()
params = st.query_params

if "save" in params:
    try:
        t = int(params.get("time", 0))
        s = int(params.get("step", 0))
        if t > 0 and s > 0:
            save_score(t, s)
            st.success(f"🎉 成绩已保存：{t}秒，{s}步")
    except Exception as e:
        st.error(f"❌ 保存失败：{e}")
    st.rerun()
    st.query_params.clear()

if "clear" in params:
    clear_rank()
    st.success("🧹 排行榜已清空")
    st.rerun()
    st.query_params.clear()

# 最后加载排行榜数据
rank_data = load_rank()

# ===================== 前端代码（修复数据传递和提交逻辑） =====================
puzzle_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    /* 保持原有样式不变 */
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:#f0f0f0;padding:10px;font-family: "Microsoft YaHei";}
    .button-row {display: flex;justify-content: center;gap: 12px;margin: 10px 0;width: 100%;}
    button {padding: 10px 16px;border: none;border-radius: 6px;background: #667eea;color: white;font-size: 14px;cursor: pointer;white-space: nowrap;}
    button:hover {background: #5568d3;}
    select {padding: 8px 12px;border-radius: 6px;border: none;font-size: 14px;}
    .info{text-align:center;font-weight:bold;margin:10px 0;font-size:16px;}
    .puzzle{max-width:320px;margin:0 auto;}
    .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:2px;background:#333;padding:2px;border-radius:8px;aspect-ratio:1;}
    .tile{background:#fff;background-size:300% 300%;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:24px;color:#fff;text-shadow:0 0 2px #000;}
    .tile.empty{background:#333!important;}
    .tile.movable{box-shadow:0 0 5px #4ECDC4;}
    .rank-container{max-width:320px;margin:15px auto;display:flex;gap:10px;}
    .rank-box{flex:1;background:#fff;padding:10px;border-radius:8px;text-align:center;}
    .rank-title{font-weight:bold;color:#667eea;margin-bottom:5px;}
    .rank-item{font-size:12px;padding:3px 0;}
    .clear-btn{display:block;margin:10px auto;background:#ff6b6b;}
</style>
</head>
<body>
    <!-- 保持原有HTML结构不变 -->
    <div class="button-row">
        <button onclick="shufflePuzzle()">🔀 打乱</button>
        <button onclick="autoSolve()">🤖 自动还原</button>
    </div>
    <div class="button-row">
        <button onclick="prevImage()">⬅️ 上一张</button>
        <button onclick="nextImage()">➡️ 下一张</button>
        <select id="imageSelect" onchange="selectImage(this.value)"></select>
    </div>
    <div class="info">步数：<span id="moves">0</span>  时长：<span id="time">00:00</span></div>
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

let board = [];
let squareImg = "";
let moves = 0;
let isSolving = false;
let currentImageIndex = 0;
const imageCache = {};
let manualPlay = true;

let startTime = 0;
let timer = null;
let elapsedTime = 0;

const SERVER_TIME_RANK = SERVER_TIME_RANK_PLACEHOLDER;
const SERVER_STEP_RANK = SERVER_STEP_RANK_PLACEHOLDER;

function formatTime(seconds) {
    const min = Math.floor(seconds / 60).toString().padStart(2, '0');
    const sec = (seconds % 60).toString().padStart(2, '0');
    return `${min}:${sec}`;
}

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
    document.getElementById("time").textContent = "00:00";
}

async function cropSquare(url){
    if(imageCache[url]) return imageCache[url];
    return new Promise(res=>{
        const img = new Image();
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
        img.onerror = () => {
            const canvas = document.createElement('canvas');
            canvas.width = canvas.height = 300;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#667eea';
            ctx.fillRect(0,0,300,300);
            const data = canvas.toDataURL();
            imageCache[url] = data;
            res(data);
        };
        img.src = url;
    });
}

const getEmptyIndex = () => board.findIndex(v => v === 0);
const isSolved = () => JSON.stringify(board) === JSON.stringify(target);

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

    // 手动通关触发提交
    if(isSolved() && timer && manualPlay){
        stopTimer();
        submitScore();
    }
}

function move(index){
    const emptyIdx = getEmptyIndex();
    [board[index], board[emptyIdx]] = [board[emptyIdx], board[index]];
    moves++;
    render();
}

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

async function selectImage(index){
    currentImageIndex = parseInt(index);
    board = [...target];
    moves = 0;
    resetTimer();
    isSolving = false;
    manualPlay = true;
    squareImg = await cropSquare(IMAGE_LIST[currentImageIndex]);
    render();
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

function shufflePuzzle(){
    moves = 0;
    resetTimer();
    manualPlay = true;
    autoShuffleBoard();
}

// 修复：使用parent.location确保参数被Streamlit捕获
function submitScore() {
    if(elapsedTime <= 0 || moves <= 0) return;
    alert("你真是个棒人！！");
    // 关键修复：使用window.parent.location.href
    const url = new URL(window.parent.location.href);
    url.searchParams.set('save', '1');
    url.searchParams.set('time', elapsedTime);
    url.searchParams.set('step', moves);
    url.searchParams.set('t', Date.now()); // 避免缓存
    window.parent.location.href = url.toString();
}

function clearRank() {
    const url = new URL(window.parent.location.href);
    url.searchParams.set('clear', '1');
    url.searchParams.set('t', Date.now());
    window.parent.location.href = url.toString();
}

// 修复：添加空数据处理和调试输出
function renderServerRank() {
    console.log("服务器时间排行数据：", SERVER_TIME_RANK);
    console.log("服务器步数排行数据：", SERVER_STEP_RANK);
    const timeDom = document.getElementById('timeRank');
    const stepDom = document.getElementById('stepRank');
    
    if (SERVER_TIME_RANK.length === 0) {
        timeDom.innerHTML = '<div class="rank-item">暂无数据</div>';
    } else {
        timeDom.innerHTML = SERVER_TIME_RANK.map((item, i) => 
            `<div class="rank-item">${i+1}. ${item.text}</div>`
        ).join('');
    }
    
    if (SERVER_STEP_RANK.length === 0) {
        stepDom.innerHTML = '<div class="rank-item">暂无数据</div>';
    } else {
        stepDom.innerHTML = SERVER_STEP_RANK.map((item, i) => 
            `<div class="rank-item">${i+1}. ${item.step}步</div>`
        ).join('');
    }
}

async function autoSolve(){
    if(isSolved() || isSolving) return;
    isSolving = true;
    manualPlay = false;

    const queue = [{state:[...board], space:getEmptyIndex(), steps:[]}];
    const visited = new Set([JSON.stringify(board)]);

    while(queue.length){
        const cur = queue.shift();
        if(JSON.stringify(cur.state) === JSON.stringify(target)){
            await executeSteps(cur.steps);
            isSolving = false;
            stopTimer();
            alert("你是不是不行，还得自动还原。");
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

async function executeSteps(steps){
    for(const pos of steps){
        move(pos);
        await new Promise(r => setTimeout(r, 120));
    }
}

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

# 修复：使用json.dumps确保数据格式正确
image_list_str = json.dumps(image_base64_list)
image_names_str = json.dumps(image_files)
time_rank_str = json.dumps(rank_data["time_rank"], ensure_ascii=False)
step_rank_str = json.dumps(rank_data["step_rank"], ensure_ascii=False)

puzzle_html = puzzle_html.replace('IMAGE_LIST_PLACEHOLDER', image_list_str)
puzzle_html = puzzle_html.replace('IMAGE_NAMES_PLACEHOLDER', image_names_str)
puzzle_html = puzzle_html.replace('SERVER_TIME_RANK_PLACEHOLDER', time_rank_str)
puzzle_html = puzzle_html.replace('SERVER_STEP_RANK_PLACEHOLDER', step_rank_str)

components.html(puzzle_html, height=900)

st.write("---")
st.write("💡 规则：开局默认打乱 | 自动还原不计成绩 | 手动通关上榜")