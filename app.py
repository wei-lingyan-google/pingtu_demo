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

# ===================== 排行榜数据（云端用session_state） =====================
if "rank_data" not in st.session_state:
    st.session_state.rank_data = {"time_rank": [], "step_rank": []}

# ===================== 图片加载 =====================
image_files = []
if os.path.exists('images'):
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
    except Exception:
        continue

# 兜底图片
if not image_base64_list:
    img = Image.new('RGB', (300, 300), color=(102, 126, 234))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    image_base64_list = [f'data:image/jpeg;base64,{b64}']
    image_files = ["默认图片.jpg"]

# ===================== 核心：处理URL参数（先处理，再渲染页面） =====================
params = st.query_params

# 保存成绩逻辑（必须放在最前面）
if "save" in params:
    try:
        t = int(params.get("time", 0))
        s = int(params.get("step", 0))
        if t > 0 and s > 0:
            # 保存到session_state排行榜
            st.session_state.rank_data["time_rank"].append({
                "time": t,
                "text": f"{t//60:02d}:{t%60:02d}"
            })
            st.session_state.rank_data["step_rank"].append({"step": s})
            
            # 排序并保留前5名
            st.session_state.rank_data["time_rank"] = sorted(
                st.session_state.rank_data["time_rank"],
                key=lambda x: x["time"]
            )[:5]
            st.session_state.rank_data["step_rank"] = sorted(
                st.session_state.rank_data["step_rank"],
                key=lambda x: x["step"]
            )[:5]
            
            # 显示绿色提示条
            st.success(f"🎉 成绩已上榜！{t//60:02d}:{t%60:02d} | {s}步")
    except Exception as e:
        st.error(f"❌ 保存失败：{e}")
    # 清除参数并刷新页面
    st.query_params.clear()
    st.rerun()

# 清空排行榜逻辑
if "clear" in params:
    st.session_state.rank_data = {"time_rank": [], "step_rank": []}
    st.success("🧹 排行榜已清空")
    st.query_params.clear()
    st.rerun()

# ===================== 前端HTML游戏代码（修复通信方式，删除错误API） =====================
puzzle_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
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
        <div class="rank-box"><div class="rank-title">🏆 最短时间</div><div id="timeRank"></div></div>
        <div class="rank-box"><div class="rank-title">🏆 最少步数</div><div id="stepRank"></div></div>
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
            imageCache[url] = canvas.toDataURL();
            res(imageCache[url]);
        };
        img.onerror = () => {
            const canvas = document.createElement('canvas');
            canvas.width = canvas.height = 300;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#667eea';
            ctx.fillRect(0,0,300,300);
            imageCache[url] = canvas.toDataURL();
            res(imageCache[url]);
        };
        img.src = url;
    });
}

const getEmptyIndex = () => board.findIndex(v => v === 0);
const isSolved = () => JSON.stringify(board) === JSON.stringify(target);

function render(){
    const grid = document.getElementById('grid');
    const emptyIdx = getEmptyIndex();
    grid.innerHTML = '';
    for(let i=0;i<9;i++){
        const tile = document.createElement('div');
        const val = board[i];
        if(val === 0){ tile.className = 'tile empty'; }
        else{
            tile.className = 'tile';
            tile.textContent = val;
            const idx = val-1;
            tile.style.backgroundImage = `url(${squareImg})`;
            tile.style.backgroundPosition = `${idx%3*50}% ${Math.floor(idx/3)*50}%`;
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
    if(isSolved() && timer && manualPlay){ stopTimer(); submitScore(); }
}

function move(index){
    const e = getEmptyIndex();
    [board[index], board[e]] = [board[e], board[index]];
    moves++;
    render();
}

function initImageSelect(){
    const s = document.getElementById('imageSelect');
    s.innerHTML = '';
    IMAGE_NAMES.forEach((n,i)=>{
        const o = document.createElement('option');
        o.value=i; o.textContent=n.replace(/\.\w+$/,'');
        if(i===currentImageIndex) o.selected=true;
        s.appendChild(o);
    });
}

async function selectImage(i){
    currentImageIndex=parseInt(i);
    board=[...target]; moves=0; resetTimer(); isSolving=false; manualPlay=true;
    squareImg=await cropSquare(IMAGE_LIST[currentImageIndex]);
    render(); autoShuffleBoard();
}
function prevImage(){ selectImage((currentImageIndex-1+IMAGE_LIST.length)%IMAGE_LIST.length); }
function nextImage(){ selectImage((currentImageIndex+1)%IMAGE_LIST.length); }

function autoShuffleBoard(){
    for(let i=0;i<70;i++){
        const e=getEmptyIndex();
        const dirs=[-1,1,-3,3].filter(d=>{
            const n=e+d;
            if(n<0||n>=9) return false;
            if(e%3===0&&d===-1) return false;
            if(e%3===2&&d===1) return false;
            return true;
        });
        if(dirs.length){
            const r=dirs[Math.floor(Math.random()*dirs.length)];
            [board[e],board[e+r]]=[board[e+r],board[e]];
        }
    }
    render(); startTimer();
}

function shufflePuzzle(){ moves=0; resetTimer(); manualPlay=true; autoShuffleBoard(); }

// ===================== 修复：改用URL传参，彻底删除错误API =====================
function submitScore() {
    if(elapsedTime<=0||moves<=0) return;
    alert("你真是个棒人！！");
    // 直接跳转到当前页面，带上成绩参数
    const url = new URL(window.parent.location.href);
    url.searchParams.set('save', '1');
    url.searchParams.set('time', elapsedTime);
    url.searchParams.set('step', moves);
    url.searchParams.set('t', Date.now()); // 防止缓存
    window.parent.location.href = url.toString();
}

function clearRank() {
    const url = new URL(window.parent.location.href);
    url.searchParams.set('clear', '1');
    url.searchParams.set('t', Date.now());
    window.parent.location.href = url.toString();
}

function renderServerRank() {
    const t=document.getElementById('timeRank'),s=document.getElementById('stepRank');
    t.innerHTML=SERVER_TIME_RANK.length?SERVER_TIME_RANK.map((i,j)=>`<div class="rank-item">${j+1}. ${i.text}</div>`).join(''):'<div class="rank-item">暂无数据</div>';
    s.innerHTML=SERVER_STEP_RANK.length?SERVER_STEP_RANK.map((i,j)=>`<div class="rank-item">${j+1}. ${i.step}步</div>`).join(''):'<div class="rank-item">暂无数据</div>';
}

async function autoSolve(){
    if(isSolved()||isSolving) return;
    isSolving=true; manualPlay=false;
    const q=[{state:[...board],space:getEmptyIndex(),steps:[]}];
    const v=new Set([JSON.stringify(board)]);
    while(q.length){
        const c=q.shift();
        if(JSON.stringify(c.state)===JSON.stringify(target)){
            await executeSteps(c.steps);
            isSolving=false; stopTimer();
            alert("你是不是不行，还得自动还原。");
            return;
        }
        const x=Math.floor(c.space/3),y=c.space%3;
        for(let i=0;i<4;i++){
            const nx=x+dx[i],ny=y+dy[i];
            if(nx<0||nx>=3||ny<0||ny>=3) continue;
            const ns=nx*3+ny;
            const nst=[...c.state];
            [nst[c.space],nst[ns]]=[nst[ns],nst[c.space]];
            const k=JSON.stringify(nst);
            if(!v.has(k)){v.add(k);q.push({state:nst,space:ns,steps:[...c.steps,ns]});}
        }
    }
    isSolving=false;
}
async function executeSteps(s){for(const p of s){move(p);await new Promise(r=>setTimeout(r,120));}}

const IMAGE_LIST = IMAGE_LIST_PLACEHOLDER;
const IMAGE_NAMES = IMAGE_NAMES_PLACEHOLDER;
async function init(){ initImageSelect(); renderServerRank(); await selectImage(0); }
init();
</script>
</body>
</html>
"""

# ===================== 数据注入（使用session_state的最新数据） =====================
image_list_str = json.dumps(image_base64_list)
image_names_str = json.dumps(image_files)
time_rank_str = json.dumps(st.session_state.rank_data["time_rank"], ensure_ascii=False)
step_rank_str = json.dumps(st.session_state.rank_data["step_rank"], ensure_ascii=False)

puzzle_html = puzzle_html.replace('IMAGE_LIST_PLACEHOLDER', image_list_str)
puzzle_html = puzzle_html.replace('IMAGE_NAMES_PLACEHOLDER', image_names_str)
puzzle_html = puzzle_html.replace('SERVER_TIME_RANK_PLACEHOLDER', time_rank_str)
puzzle_html = puzzle_html.replace('SERVER_STEP_RANK_PLACEHOLDER', step_rank_str)

# ===================== 渲染游戏 =====================
components.html(puzzle_html, height=900, key="puzzle_game")

st.write("---")
st.write("💡 规则：开局默认打乱 | 自动还原不计成绩 | 手动通关上榜")