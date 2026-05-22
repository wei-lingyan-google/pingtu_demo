# app.py
import streamlit as st
import streamlit.components.v1 as components
import os
import base64

st.title("🧩 钧崽变变变")
st.write("✅ 点击空格相邻方块移动 | BFS最短路径自动还原")

# 读取图片 + 修复所有语法错误
image_files = [f for f in os.listdir('images') if f.endswith(('.jpg', '.jpeg', '.png'))]
# 修复排序语法
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

# 🔥 彻底修复：空格不消失 + 自动还原不卡死 + BFS严格对齐C++代码
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
        <button onclick="autoSolve()">自动还原</button>
    </div>
    <div class="info">步数：<span id="moves">0</span></div>
    <div class="puzzle"><div class="grid" id="grid"></div></div>

<script>
const N = 3;
const target = [1,2,3,4,5,6,7,8,0]; // 0=空格（严格对应C++代码）
const dx = [-1,1,0,0]; // 上下左右 对应C++ dx
const dy = [0,0,-1,1];

let board = [];    // 拼图数据
let squareImg = "";// 裁剪后的正方形图片
let moves = 0;
let isSolving = false; // 防止重复点击卡死

// 居中裁剪正方形（上下裁剪）
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

// 获取空格位置（值为0）
function getEmptyIndex(){
    return board.findIndex(v => v === 0);
}

// 检查是否完成
function isSolved(){
    return JSON.stringify(board) === JSON.stringify(target);
}

// 渲染拼图（核心：保证空格永远显示）
function render(){
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    const emptyIdx = getEmptyIndex();

    for(let i=0;i<9;i++){
        const tile = document.createElement('div');
        const val = board[i];

        if(val === 0){ // 空格
            tile.className = 'tile empty';
        }else{
            tile.className = 'tile';
            tile.textContent = val;
            // 正确分块显示图片
            const idx = val - 1;
            const col = idx % 3;
            const row = Math.floor(idx / 3);
            tile.style.backgroundImage = `url(${squareImg})`;
            tile.style.backgroundPosition = `${col*50}% ${row*50}%`;

            // 判断可移动
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
}

// 移动方块（安全移动，保证空格不消失）
function move(index){
    const emptyIdx = getEmptyIndex();
    [board[index], board[emptyIdx]] = [board[emptyIdx], board[index]];
    moves++;
    render();
}

// 还原：正方形裁剪 → 9格 → 编号1-8 → 0=空格（右下角）
async function resetPuzzle(){
    board = [...target];
    moves = 0;
    isSolving = false;
    squareImg = await cropSquare(IMAGE_LIST[0]);
    render();
}

// 打乱拼图（保证可解）
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
        render();
    });
}

// ====================== 修复版BFS自动还原（严格对齐C++，无卡死）======================
async function autoSolve(){
    if(isSolved() || isSolving) return;
    isSolving = true;

    // BFS节点
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

        // 找到答案，执行步骤
        if(JSON.stringify(cur.state) === JSON.stringify(target)){
            await executeSteps(cur.steps);
            isSolving = false;
            return;
        }

        const x = Math.floor(cur.space / 3);
        const y = cur.space % 3;

        // 四个方向（严格对应C++）
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
    isSolving = false;
}

// 安全执行移动步骤（永不卡死、空格永不消失）
async function executeSteps(steps){
    for(const pos of steps){
        move(pos);
        await new Promise(r => setTimeout(r, 200));
    }
}

// 初始化
const IMAGE_LIST = IMAGE_LIST_PLACEHOLDER;
resetPuzzle();
</script>
</body>
</html>
"""

# 注入图片列表
image_list_str = '["' + '", "'.join(image_base64_list) + '"]'
puzzle_html = puzzle_html.replace('IMAGE_LIST_PLACEHOLDER', image_list_str)
components.html(puzzle_html, height=650)

st.write("---")
st.write("💡 规则：还原=正方形裁剪+9格分块+编号1-8；自动还原采用BFS最短路径")