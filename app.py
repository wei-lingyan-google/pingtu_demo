# app.py
import streamlit as st
import streamlit.components.v1 as components
import os
import base64

st.title("🧩 钧崽变变变")
st.write("✅ 还原状态不可操作 | 打乱后可玩 | 换图+排行榜")

# 读取图片（已修复排序语法）
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

# 核心拼图HTML（仅新增功能，核心逻辑完全不变）
puzzle_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:#f0f0f0;padding:10px;font-family: "Microsoft YaHei"}
    .btn-group{display:flex;justify-content:center;gap:10px;margin:10px 0;flex-wrap:wrap}
    button{padding:8px 16px;border:none;border-radius:6px;background:#667eea;color:white;cursor:pointer}
    button:hover{background:#5568d3}
    .info{text-align:center;font-weight:bold;margin:5px 0}
    .puzzle{max-width:350px;margin:10px auto}
    .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:3px;background:#333;padding:3px;border-radius:8px;aspect-ratio:1}
    .tile{
        background:#fff;background-size:300% 300%;border-radius:4px;
        display:flex;align-items:center;justify-content:center;
        font-size:28px;font-weight:bold;color:#fff;text-shadow:0 0 4px #000;
        cursor:pointer
    }
    .tile.empty{background:#333!important;color:transparent}
    .tile.movable{box-shadow:0 0 8px #4ECDC4}
    /* 排行榜样式 */
    .leaderboard{margin-top:20px;padding:15px;background:white;border-radius:10px;box-shadow:0 4px 12px rgba(0,0,0,0.1);max-width:350px;margin:20px auto}
    .leaderboard h3{text-align:center;margin-bottom:10px;color:#333}
    .leaderboard table{width:100%;border-collapse:collapse}
    .leaderboard th,.leaderboard td{padding:8px;text-align:center;border-bottom:1px solid #eee}
    /* 胜利弹窗样式 */
    .overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:999}
    .win-popup{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;padding:25px;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.2);text-align:center;z-index:1000}
    .win-popup.show,.overlay.show{display:block}
    .win-popup button{margin-top:15px;padding:10px 25px;background:#4CAF50;color:white;border:none;border-radius:6px;cursor:pointer}
</style>
</head>
<body>
    <div class="btn-group">
        <button onclick="resetPuzzle()">还原</button>
        <button onclick="shufflePuzzle()">打乱</button>
        <button onclick="autoSolve()">自动还原</button>
        <button onclick="changeImage()">换图</button>
    </div>
    <div class="info">⏱️ <span id="timer">00:00</span> &nbsp;&nbsp; 👣 <span id="moves">0</span></div>
    <div class="puzzle"><div class="grid" id="grid"></div></div>

    <!-- 排行榜 -->
    <div class="leaderboard">
        <h3>🏆 排行榜</h3>
        <table>
            <thead><tr><th>排名</th><th>用时</th><th>步数</th></tr></thead>
            <tbody id="leaderboardBody"></tbody>
        </table>
    </div>

    <!-- 胜利弹窗 -->
    <div class="overlay" id="overlay"></div>
    <div class="win-popup" id="winPopup">
        <h2>🎉 恭喜完成！</h2>
        <p>用时: <span id="finalTime">00:00</span></p>
        <p>步数: <span id="finalMoves">0</span></p>
        <button onclick="closeWinPopup()">再来一局</button>
    </div>

<script>
const N = 3;
const target = [1,2,3,4,5,6,7,8,0]; // 0=空格（核心逻辑不变）
const dx = [-1,1,0,0]; // 上下左右（核心逻辑不变）
const dy = [0,0,-1,1];

let board = [];    // 拼图数据（核心逻辑不变）
let squareImg = "";// 裁剪后的正方形图片（核心逻辑不变）
let moves = 0;
let timer = 0;
let timerInterval = null;
let isPlaying = false;       // 还原状态不可玩（新增）
let isAutoSolving = false;   // 自动还原标记（新增）
let currentImageIndex = 0;   // 当前图片索引（新增）

// 居中裁剪正方形（核心逻辑不变）
function cropSquare(url){
    return new Promise(res=>{
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.onload = ()=>{
            const size = Math.min(img.width, img.height);
            const canvas = document.createElement('canvas');
            canvas.width = canvas.height = size;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, (img.width-size)/2, (img.height-size)/2, size, size, 0,0,size,size);
            res(canvas.toDataURL());
        };
        img.src = url;
    });
}

// 获取空格位置（核心逻辑不变）
function getEmptyIndex(){
    return board.findIndex(v => v === 0);
}

// 检查是否完成（核心逻辑不变）
function isSolved(){
    return JSON.stringify(board) === JSON.stringify(target);
}

// 渲染拼图（新增：还原状态不可点击）
function render(){
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    const emptyIdx = getEmptyIndex();

    for(let i=0;i<9;i++){
        const tile = document.createElement('div');
        const val = board[i];

        if(val === 0){ // 空格（核心逻辑不变）
            tile.className = 'tile empty';
        }else{
            tile.className = 'tile';
            tile.textContent = val;
            // 正确分块显示图片（核心逻辑不变）
            const idx = val - 1;
            const col = idx % 3;
            const row = Math.floor(idx / 3);
            tile.style.backgroundImage = `url(${squareImg})`;
            tile.style.backgroundPosition = `${col*50}% ${row*50}%`;

            // 新增：只有isPlaying为true时才可点击
            if(isPlaying && Math.abs(Math.floor(emptyIdx/3)-Math.floor(i/3)) + Math.abs(emptyIdx%3 - i%3) === 1){
                tile.classList.add('movable');
                tile.onclick = () => move(i);
            }
        }
        grid.appendChild(tile);
    }
    document.getElementById('moves').textContent = moves;
}

// 移动方块（核心逻辑不变，新增状态判断）
function move(index){
    if(!isPlaying || isAutoSolving) return; // 还原/自动还原状态禁止移动
    const emptyIdx = getEmptyIndex();
    [board[index], board[emptyIdx]] = [board[emptyIdx], board[index]];
    moves++;
    document.getElementById('moves').textContent = moves;
    render();
    // 完成时保存分数（自动还原除外）
    if(isSolved()){
        stopTimer();
        if(!isAutoSolving){
            saveScore(timer, moves);
            showWinPopup();
        }
    }
}

// 计时器控制（新增）
function startTimer(){
    stopTimer();
    timerInterval = setInterval(()=>{
        timer++;
        const m = Math.floor(timer/60).toString().padStart(2,'0');
        const s = (timer%60).toString().padStart(2,'0');
        document.getElementById('timer').textContent = `${m}:${s}`;
    }, 1000);
}
function stopTimer(){
    if(timerInterval){
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

// 还原：仅展示顺序图，不可操作（核心逻辑不变，新增状态控制）
async function resetPuzzle(){
    board = [...target];
    moves = 0;
    timer = 0;
    isPlaying = false; // 还原状态不可玩
    isAutoSolving = false;
    stopTimer();
    document.getElementById('moves').textContent = '0';
    document.getElementById('timer').textContent = '00:00';
    squareImg = await cropSquare(IMAGE_LIST[currentImageIndex]);
    render();
}

// 打乱拼图：打乱后可玩（核心逻辑不变，新增状态控制）
function shufflePuzzle(){
    resetPuzzle().then(()=>{
        for(let i=0;i<100;i++){
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
        isPlaying = true; // 打乱后可玩
        startTimer(); // 开始计时
        render();
    });
}

// ====================== BFS自动还原（核心逻辑不变，新增状态控制）======================
async function autoSolve(){
    if(isSolved() || isAutoSolving || !isPlaying) return; // 还原状态禁止自动还原
    isAutoSolving = true;
    stopTimer(); // 自动还原不记录时间

    class Node {
        constructor(state, space, steps){
            this.state = [...state];
            this.space = space;
            this.steps = steps || [];
        }
    }

    const queue = [new Node(board, getEmptyIndex(), [])];
    const visited = new Set([JSON.stringify(board)]);

    while(queue.length > 0){
        const cur = queue.shift();

        if(JSON.stringify(cur.state) === JSON.stringify(target)){
            await executeSteps(cur.steps);
            isAutoSolving = false;
            render();
            return;
        }

        const x = Math.floor(cur.space / 3);
        const y = cur.space % 3;

        for(let i=0;i<4;i++){
            const nx = x + dx[i];
            const ny = y + dy[i];
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
    isAutoSolving = false;
}

// 安全执行移动步骤（核心逻辑不变）
async function executeSteps(steps){
    for(const pos of steps){
        move(pos);
        await new Promise(r => setTimeout(r, 200));
    }
}

// 换图功能（新增）
function changeImage(){
    currentImageIndex = (currentImageIndex + 1) % IMAGE_LIST.length;
    resetPuzzle();
}

// 排行榜相关（新增）
function saveScore(time, moves){
    let scores = JSON.parse(localStorage.getItem('puzzleScores') || '[]');
    scores.push({time: time, moves: moves});
    // 按时间升序、步数升序排序
    scores.sort((a,b) => a.time - b.time || a.moves - b.moves);
    // 保留前10名
    localStorage.setItem('puzzleScores', JSON.stringify(scores.slice(0,10)));
    loadLeaderboard();
}
function loadLeaderboard(){
    const scores = JSON.parse(localStorage.getItem('puzzleScores') || '[]');
    const tbody = document.getElementById('leaderboardBody');
    tbody.innerHTML = scores.length ? scores.map((s,i)=>{
        const m = Math.floor(s.time/60).toString().padStart(2,'0');
        const sStr = (s.time%60).toString().padStart(2,'0');
        const icon = i===0?'🥇':i===1?'🥈':i===2?'🥉':i+1;
        return `<tr><td>${icon}</td><td>${m}:${sStr}</td><td>${s.moves}</td></tr>`;
    }).join('') : '<tr><td colspan="3">暂无记录</td></tr>';
}

// 胜利弹窗相关（新增）
function showWinPopup(){
    const m = Math.floor(timer/60).toString().padStart(2,'0');
    const s = (timer%60).toString().padStart(2,'0');
    document.getElementById('finalTime').textContent = `${m}:${s}`;
    document.getElementById('finalMoves').textContent = moves;
    document.getElementById('overlay').classList.add('show');
    document.getElementById('winPopup').classList.add('show');
}
function closeWinPopup(){
    document.getElementById('overlay').classList.remove('show');
    document.getElementById('winPopup').classList.remove('show');
    shufflePuzzle();
}

// 初始化
const IMAGE_LIST = IMAGE_LIST_PLACEHOLDER;
loadLeaderboard(); // 加载排行榜
resetPuzzle();
</script>
</body>
</html>
"""

# 注入图片列表
image_list_str = '["' + '", "'.join(image_base64_list) + '"]'
puzzle_html = puzzle_html.replace('IMAGE_LIST_PLACEHOLDER', image_list_str)

components.html(puzzle_html, height=900)

st.write("---")
st.write("💡 规则：还原=仅展示不可操作；打乱后可玩并计时；自动还原不计入榜单；点击换图切换images目录下的图片")