# app.py
import streamlit as st
import streamlit.components.v1 as components
import os
import base64

st.title("🧩 钧崽变变变")
st.write("✅ 点击空格相邻方块移动 | 基于BFS最短路径自动还原")

# 读取图片 + 修复排序语法错误
image_files = [f for f in os.listdir('images') if f.endswith(('.jpg', '.jpeg', '.png'))]
image_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit, x) else 0)

image_base64_list = []
for img_file in image_files:
    try:
        with open(os.path.join('images', img_file), 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
            ext = img_file.split('.')[-1]
            mime = 'image/jpeg' if ext in ('jpg','jpeg') else 'image/png'
            image_base64_list.append(f'data:{mime};base64,{b64}')
    except Exception as e:
        st.error(f"加载失败：{e}")
if not image_base64_list:
    image_base64_list = ["https://picsum.photos/300"]

# 核心：BFS自动还原 + 正确拼图逻辑
puzzle_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:#f0f0f0;padding:10px;font-family: "Microsoft YaHei"}
    .btn-group{display:flex;justify-content:center;gap:10px;margin:10px 0}
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
</style>
</head>
<body>
    <div class="btn-group">
        <button onclick="resetPuzzle()">还原</button>
        <button onclick="shufflePuzzle()">打乱</button>
        <button onclick="autoSolveByBFS()">自动还原</button>
    </div>
    <div class="info">步数：<span id="moves">0</span></div>
    <div class="puzzle"><div class="grid" id="grid"></div></div>

<script>
const N = 3;
const N2 = 9;
// 对应C++：上下左右移动
const dx = [0, 0, -1, 1]; 
const dy = [1, -1, 0, 0];

let tiles = [1,2,3,4,5,6,7,8,9]; // 9=空格
let squareImg = "";
let moves = 0;
const target = [1,2,3,4,5,6,7,8,9]; // 正确目标

// 居中裁剪正方形（上下/左右裁剪）
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

// 获取空格位置（值为9）
function getEmptyPos(){ return tiles.findIndex(v=>v===9) }

// 检查是否完成
function isWin(){ return JSON.stringify(tiles) === JSON.stringify(target) }

// 渲染拼图
function render(){
    const g = document.getElementById('grid');
    g.innerHTML = '';
    const empty = getEmptyPos();
    for(let i=0;i<N2;i++){
        const t = document.createElement('div');
        const val = tiles[i];
        if(val === 9){
            t.className = 'tile empty';
        }else{
            t.className = 'tile';
            t.textContent = val;
            // 正确分块显示
            const idx = val - 1;
            const col = idx % 3;
            const row = Math.floor(idx / 3);
            t.style.backgroundImage = `url(${squareImg})`;
            t.style.backgroundPosition = `${col*50}% ${row*50}%`;
            
            // 判断可移动
            const ex = Math.floor(empty/3), ey = empty%3;
            const ix = Math.floor(i/3), iy = i%3;
            if(Math.abs(ex-ix)+Math.abs(ey-iy)===1){
                t.classList.add('movable');
                t.onclick = ()=> move(i);
            }
        }
        g.appendChild(t);
    }
    document.getElementById('moves').textContent = moves;
}

// 移动方块
function move(idx){
    const empty = getEmptyPos();
    [tiles[idx], tiles[empty]] = [tiles[empty], tiles[idx]];
    moves++;
    render();
}

// 重置：正确拼图（裁正方形→9格→1-8编号→9空格）
async function resetPuzzle(){
    tiles = [...target];
    moves = 0;
    squareImg = await cropSquare(IMAGE_LIST[0]);
    render();
}

// 打乱拼图（可解）
function shufflePuzzle(){
    resetPuzzle().then(()=>{
        for(let i=0;i<150;i++){
            const e = getEmptyPos();
            const dirs = [-1,1,-3,3].filter(d=>{
                const n = e+d;
                if(n<0||n>=9) return false;
                if(e%3===0&&d===-1) return false;
                if(e%3===2&&d===1) return false;
                return true;
            });
            const r = dirs[Math.floor(Math.random()*dirs.length)];
            [tiles[e], tiles[e+r]] = [tiles[e+r], tiles[e]];
        }
        render();
    });
}

// ====================== BFS 自动还原（完全参考你的C++代码）======================
async function autoSolveByBFS(){
    if(isWin()) return;
    
    // BFS节点结构
    class Node {
        constructor(state, space, path){
            this.state = [...state];
            this.space = space;
            this.path = path || "";
        }
    }

    const queue = [];
    const visited = new Set();
    const startState = [...tiles];
    const startSpace = getEmptyPos();
    
    queue.push(new Node(startState, startSpace, ""));
    visited.add(JSON.stringify(startState));

    while(queue.length > 0){
        const cur = queue.shift();
        
        // 找到目标，执行路径
        if(JSON.stringify(cur.state) === JSON.stringify(target)){
            await runPath(cur.path);
            return;
        }

        const sx = Math.floor(cur.space / N);
        const sy = cur.space % N;

        // 四个方向遍历（对应C++逻辑）
        for(let i=0;i<4;i++){
            const tx = sx + dx[i];
            const ty = sy + dy[i];
            if(tx<0||tx>=N||ty<0||ty>=N) continue;

            const newSpace = tx * N + ty;
            const newState = [...cur.state];
            
            // 交换空格（对应C++ swap）
            [newState[cur.space], newState[newSpace]] = [newState[newSpace], newState[cur.space]];
            const key = JSON.stringify(newState);

            if(!visited.has(key)){
                visited.add(key);
                queue.push(new Node(newState, newSpace, cur.path + i));
            }
        }
    }
}

// 执行BFS找到的路径
async function runPath(path){
    for(let i=0;i<path.length;i++){
        const dir = parseInt(path[i]);
        const empty = getEmptyPos();
        const sx = Math.floor(empty / N);
        const sy = empty % N;
        const tx = sx + dx[dir];
        const ty = sy + dy[dir];
        const newPos = tx * N + ty;
        
        move(newPos);
        await new Promise(r=>setTimeout(r,200));
    }
}

// 初始化
IMAGE_LIST = IMAGE_LIST_PLACEHOLDER;
resetPuzzle();
</script>
</body>
</html>
"""

# 注入图片
puzzle_html = puzzle_html.replace("IMAGE_LIST_PLACEHOLDER", str(image_base64_list))
components.html(puzzle_html, height=650)

st.write("---")
st.write("💡 规则：还原=正方形裁剪+9格分块+编号1-8；自动还原采用BFS最短路径算法")