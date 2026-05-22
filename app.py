import streamlit as st
import streamlit.components.v1 as components
import os
import base64
import json
from PIL import Image
import io

# 页面配置
st.set_page_config(page_title="钧崽变变变", page_icon="🧩")
st.title("🧩 钧崽变变变")
st.subheader("🎮 游戏作者：魏菱延")
st.write("✅ 点击相邻方块移动 | 自动还原不计入榜单成绩")

# ===================== 服务器排行榜文件配置（永久持久化） =====================
RANK_FILE = "puzzle_rank.json"

# 初始化文件
def init_rank():
    if not os.path.exists(RANK_FILE):
        data = {"time": [], "step": []}
        with open(RANK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# 读取排行榜
def get_rank():
    init_rank()
    with open(RANK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 保存成绩（仅手动通关调用）
def save_rank(time_sec, step_cnt):
    if time_sec <= 0 or step_cnt <= 0:
        return
    data = get_rank()
    # 添加记录
    data["time"].append({"sec": time_sec, "text": f"{time_sec//60:02d}:{time_sec%60:02d}"})
    data["step"].append({"cnt": step_cnt})
    # 排序+保留前5名
    data["time"] = sorted(data["time"], key=lambda x: x["sec"])[:5]
    data["step"] = sorted(data["step"], key=lambda x: x["cnt"])[:5]
    # 写入文件
    with open(RANK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 清空排行榜
def clear_rank():
    data = {"time": [], "step": []}
    with open(RANK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================== 图片加载（防黑屏） =====================
image_files = [f for f in os.listdir('images') if f.endswith(('.jpg', '.jpeg', '.png'))]
image_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else 0)

image_base64_list = []
for img_file in image_files:
    try:
        with open(os.path.join('images', img_file), 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
            ext = img_file.split('.')[-1]
            mime = "image/jpeg" if ext in ('jpg','jpeg') else "image/png"
            image_base64_list.append(f"data:{mime};base64,{b64}")
    except:
        pass

# 兜底纯色图，彻底防黑屏
if not image_base64_list:
    img = Image.new('RGB', (300,300), (102,126,234))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    image_base64_list = [f"data:image/jpeg;base64,{b64}"]
    image_files = ["默认图片"]

# ===================== 读取排行榜数据 =====================
rank_data = get_rank()

# ===================== 前端页面（按钮严格两行+全功能修复） =====================
puzzle_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:#f0f0f0;padding:10px;font-family: "Microsoft YaHei";}

    /* 🔥 固定两行按钮布局 */
    .row{
        display:flex;
        justify-content:center;
        gap:10px;
        margin:8px 0;
    }
    button{
        padding:9px 15px;
        border:none;
        border-radius:6px;
        background:#667eea;
        color:white;
        font-size:14px;
        cursor:pointer;
    }
    button:hover{background:#5568d3}
    select{
        padding:7px 10px;
        border-radius:6px;
        border:none;
    }

    .info{text-align:center;font-weight:bold;margin:10px 0;font-size:16px;}
    .puzzle{max-width:320px;margin:0 auto;}
    .grid{
        display:grid;grid-template-columns:repeat(3,1fr);
        gap:2px;background:#333;padding:2px;border-radius:8px;aspect-ratio:1;
    }
    .tile{
        background:#fff;background-size:300% 300%;
        border-radius:4px;display:flex;align-items:center;justify-content:center;
        font-size:24px;color:#fff;text-shadow:0 0 2px #000;
    }
    .tile.empty{background:#333!important;}
    .tile.movable{box-shadow:0 0 5px #4ECDC4;}

    /* 排行榜样式 */
    .rank-box{
        max-width:320px;margin:15px auto;display:flex;gap:10px;
    }
    .rank-item{
        flex:1;background:white;padding:10px;border-radius:8px;text-align:center;
    }
    .rank-title{font-weight:bold;color:#667eea;margin-bottom:5px;}
    .list{font-size:12px;padding:2px 0;}
    .clear{background:#ff6b6b;margin:10px auto;display:block;}
</style>
</head>
<body>
    <!-- 第一行：游戏按钮 -->
    <div class="row">
        <button onclick="shuffle()">🔀 打乱</button>
        <button onclick="autoSolve()">🤖 自动还原</button>
    </div>
    <!-- 第二行：图片切换按钮 -->
    <div class="row">
        <button onclick="prev()">⬅️ 上一张</button>
        <button onclick="next()">➡️ 下一张</button>
        <select id="sel" onchange="changeImg(this.value)"></select>
    </div>

    <div class="info">步数：<span id="step">0</span> &nbsp;&nbsp; 时长：<span id="time">00:00</span></div>
    <div class="puzzle"><div id="grid"></div></div>

    <button class="clear" onclick="clearAll()">清空排行榜</button>
    <div class="rank-box">
        <div class="rank-item">
            <div class="rank-title">🏆 最短时间</div>
            <div id="timeList"></div>
        </div>
        <div class="rank-item">
            <div class="rank-title">🏆 最少步数</div>
            <div id="stepList"></div>
        </div>
    </div>

<script>
// 基础配置
const target = [1,2,3,4,5,6,7,8,0];
const dirs = [-1,1,-3,3];
let board, squareImg, moves=0, idx=0;
let timer=null, start=0, useTime=0;
let manualPlay = true; // 手动/自动标记：自动=false 不计分
const imgCache = {};

// 服务器排行榜数据
const timeRank = TIME_RANK;
const stepRank = STEP_RANK;

// 格式化时间
const fmt = s => `${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toString().padStart(2,'0')}`;

// 计时
function startTimer(){
    clearInterval(timer);
    start = Date.now() - useTime*1000;
    timer = setInterval(()=>{
        useTime = Math.floor((Date.now()-start)/1000);
        document.getElementById('time').innerText = fmt(useTime);
    },1000);
}
function stopTimer(){ clearInterval(timer); }
function resetTimer(){ stopTimer(); useTime=0; document.getElementById('time').innerText="00:00"; }

// 图片裁剪（防黑屏）
async function crop(url){
    if(imgCache[url]) return imgCache[url];
    return new Promise(res=>{
        const img = new Image();
        img.onload = ()=>{
            const s = Math.min(img.width,img.height);
            const c = document.createElement('canvas');
            c.width=c.height=s;
            c.getContext('2d').drawImage(img,(img.width-s)/2,(img.height-s)/2,s,s,0,0,s,s);
            imgCache[url] = c.toDataURL();
            res(imgCache[url]);
        };
        img.onerror = ()=>{
            const c = document.createElement('canvas');
            c.width=c.height=300;
            c.getContext('2d').fillStyle='#667eea';
            c.getContext('2d').fillRect(0,0,300,300);
            imgCache[url] = c.toDataURL();
            res(imgCache[url]);
        };
        img.src=url;
    });
}

// 渲染拼图
function render(){
    const g = document.getElementById('grid');
    const empty = board.findIndex(v=>v===0);
    g.innerHTML='';
    for(let i=0;i<9;i++){
        const t = document.createElement('div');
        const v = board[i];
        if(v===0) t.className='tile empty';
        else {
            t.className='tile';
            t.innerText=v;
            const x=(v-1)%3, y=Math.floor((v-1)/3);
            t.style.backgroundImage=`url(${squareImg})`;
            t.style.backgroundPosition=`${x*50}% ${y*50}%`;
            if(Math.abs(Math.floor(empty/3)-Math.floor(i/3)) + Math.abs(empty%3 - i%3) ===1){
                t.classList.add('movable');
                t.onclick=()=>move(i);
            }
        }
        g.appendChild(t);
    }
    document.getElementById('step').innerText=moves;
    // 🔥 仅手动完成才提交成绩
    if(JSON.stringify(board)===JSON.stringify(target) && timer && manualPlay){
        stopTimer();
        // 刷新页面提交成绩到服务器文件
        window.parent.postMessage({type:'save', time:useTime, step:moves}, '*');
    }
}

// 移动方块
function move(i){
    const e = board.findIndex(v=>v===0);
    [board[i],board[e]] = [board[e],board[i]];
    moves++;
    render();
}

// 打乱拼图
function shuffle(){
    resetTimer();
    moves=0;
    manualPlay=true;
    for(let i=0;i<70;i++){
        const e = board.findIndex(v=>v===0);
        const d = dirs.filter(x=>{
            const n=e+x;
            return n>=0&&n<9&&!(e%3===0&&x===-1)&&!(e%3===2&&x===1);
        });
        if(d.length) [board[e],board[e+d[Math.random()*d.length|0]]] = [board[e+d[Math.random()*d.length|0]],board[e]];
    }
    render();
    startTimer();
}

// 🔥 自动还原（标记为自动，不计分）
async function autoSolve(){
    if(JSON.stringify(board)===JSON.stringify(target)) return;
    manualPlay = false; // 关键：自动操作，不计成绩
    stopTimer();
    const q=[{s:[...board], sList:[]}];
    const v=new Set([JSON.stringify(board)]);
    while(q.length){
        const cur=q.shift();
        if(JSON.stringify(cur.s)===JSON.stringify(target)){
            for(const p of cur.sList){ move(p); await new Promise(r=>setTimeout(r,120)); }
            stopTimer();
            return;
        }
        const e=cur.s.findIndex(v=>v===0);
        const d=dirs.filter(x=>{
            const n=e+x;
            return n>=0&&n<9&&!(e%3===0&&x===-1)&&!(e%3===2&&x===1);
        });
        for(const x of d){
            const newS=[...cur.s];
            [newS[e],newS[e+x]]=[newS[e+x],newS[e]];
            const key=JSON.stringify(newS);
            if(!v.has(key)) v.add(key),q.push({s:newS,sList:[...cur.sList,e+x]});
        }
    }
}

// 图片切换
async function changeImg(i){
    idx=Number(i);
    board=[...target];
    squareImg=await crop(IMGS[idx]);
    render();
    shuffle();
}
function prev(){ changeImg((idx-1+IMGS.length)%IMGS.length); }
function next(){ changeImg((idx+1)%IMGS.length); }

// 渲染排行榜
function renderRank(){
    const t=document.getElementById('timeList'),s=document.getElementById('stepList');
    t.innerHTML=timeRank.map((i,n)=>`<div class="list">${n+1}. ${i.text}</div>`).join('');
    s.innerHTML=stepRank.map((i,n)=>`<div class="list">${n+1}. ${i.cnt}步</div>`).join('');
}

// 清空排行榜
function clearAll(){ window.parent.postMessage({type:'clear'}, '*'); }

// 初始化
const IMGS = IMG_LIST;
const NAMES = IMG_NAMES;
window.onload=async()=>{
    const sel=document.getElementById('sel');
    NAMES.forEach((n,i)=>{
        const o=document.createElement('option');
        o.value=i;o.innerText=n.replace(/\.\w+$/,'');
        sel.appendChild(o);
    });
    renderRank();
    await changeImg(0);
};

// 接收后端指令
window.addEventListener('message', e=>{
    if(e.data.type === 'refresh') window.location.reload();
});
</script>
</body>
</html>
"""

# ===================== 数据注入 + 后端通信 =====================
# 替换数据
imgs = json.dumps(image_base64_list, ensure_ascii=False)
names = json.dumps(image_files, ensure_ascii=False)
time_rank = json.dumps(rank_data["time"], ensure_ascii=False)
step_rank = json.dumps(rank_data["step"], ensure_ascii=False)

puzzle_html = puzzle_html.replace("IMG_LIST", imgs)
puzzle_html = puzzle_html.replace("IMG_NAMES", names)
puzzle_html = puzzle_html.replace("TIME_RANK", time_rank)
puzzle_html = puzzle_html.replace("STEP_RANK", step_rank)

# 监听前端消息
if "data" in st.session_state:
    msg = st.session_state.data
    if msg["type"] == "save":
        save_rank(msg["time"], msg["step"])
    if msg["type"] == "clear":
        clear_rank()
    st.session_state.pop("data")

# 渲染组件
components.html(puzzle_html, height=900)

# 隐藏的消息接收框
if st.components.v1.get_children()[0].msg:
    st.session_state.data = st.components.v1.get_children()[0].msg
    st.rerun()

st.write("---")
st.write("💡 规则：手动通关上榜 | 自动还原不计成绩 | 数据永久保存")