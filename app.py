# app.py
import streamlit as st
import streamlit.components.v1 as components
import os
import base64

st.title("🧩 钧崽变变变")
st.write("✅ 点击空格相邻方块移动；编号9永远是空格（可移动）")

# 读取本地图片
image_files = [f for f in os.listdir('images') if f.endswith(('.jpg', '.jpeg', '.png'))]
# ✅ 修复排序语法错误
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

# HTML：裁方 → 9格 → 编号1-8、编号9=空格（可移动）
puzzle_html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#f0f0f0;padding:10px;font-family: "Microsoft YaHei", sans-serif;}
.btn-group{display:flex;justify-content:center;gap:10px;margin-bottom:15px}
button{padding:8px 16px;border:none;border-radius:6px;background:#667eea;color:white;cursor:pointer}
button:hover{background:#5a6fd6}
.stats{text-align:center;font-weight:bold;margin-bottom:10px}
.puzzle-wrap{max-width:350px;margin:0 auto}
.puzzle-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:3px;background:#333;padding:3px;border-radius:6px;aspect-ratio:1}
.tile{background:#4ECDC4;background-size:300% 300%;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:bold;color:white;text-shadow:0 0 5px rgba(0,0,0,0.8);cursor:pointer}
.tile.empty{background:#333 !important;color:transparent;cursor:default}
.tile.movable{box-shadow:0 0 10px rgba(78,205,196,0.8)}
.win{text-align:center;color:#4CAF50;font-weight:bold;margin-top:10px;font-size:18px;display:none}
</style>
</head>
<body>
<div class="btn-group">
<button onclick="resetPuzzle()">还原</button>
<button onclick="shufflePuzzle()">打乱</button>
<button onclick="autoSolve()">自动还原</button>
</div>
<div class="stats">⏱️ <span id="t">00:00</span> &nbsp;&nbsp; 👣 <span id="m">0</span></div>
<div class="win" id="winMsg">🎉 拼图完成！</div>
<div class="puzzle-wrap">
<div class="puzzle-grid" id="grid"></div>
</div>

<script>
const N=3, N2=9;
let tiles = [1,2,3,4,5,6,7,8,9]; // 1-8拼图，9=固定空格编号
let moves=0, timer=0, tInterval=null;
let imgList = IMAGE_LIST_PLACEHOLDER;
let currentImg = 0;
let squareImg = '';

// 裁剪图片为正方形
function cropToSquare(url){
  return new Promise(resolve=>{
    const img=new Image();
    img.crossOrigin="anonymous";
    img.onload=()=>{
      const size=Math.min(img.width,img.height);
      const canvas=document.createElement('canvas');
      canvas.width=canvas.height=size;
      const ctx=canvas.getContext('2d');
      // 上下裁剪居中为正方形
      ctx.drawImage(img,(img.width-size)/2,(img.height-size)/2,size,size,0,0,size,size);
      resolve(canvas.toDataURL('image/jpeg'));
    };
    img.src=url;
  });
}

// 获取空格位置（值为9的位置）
function getEmptyIndex(){
  return tiles.findIndex(num=>num===9);
}

// 检查是否完成拼图
function checkWin(){
  const target = [1,2,3,4,5,6,7,8,9];
  return JSON.stringify(tiles) === JSON.stringify(target);
}

// 渲染拼图
function render(){
  const grid=document.getElementById('grid');
  grid.innerHTML='';
  const emptyIdx=getEmptyIndex();
  
  // 完成提示
  document.getElementById('winMsg').style.display = checkWin() ? 'block' : 'none';

  for(let i=0;i<N2;i++){
    const tile=document.createElement('div');
    const value=tiles[i];
    
    if(value===9){
      tile.className='tile empty';
    }else{
      tile.className='tile';
      tile.textContent=value;
      // 分割9份显示图片
      const col = i % 3;
      const row = Math.floor(i / 3);
      tile.style.backgroundImage = `url(${squareImg})`;
      tile.style.backgroundPosition = `${col * 100}% ${row * 100}%`;
      
      // 判断是否可移动
      const ex = Math.floor(emptyIdx / 3);
      const ey = emptyIdx % 3;
      const ix = Math.floor(i / 3);
      const iy = i % 3;
      if(Math.abs(ex-ix)+Math.abs(ey-iy)===1){
        tile.classList.add('movable');
        tile.onclick=()=>moveTile(i);
      }
    }
    grid.appendChild(tile);
  }
}

// 移动方块
function moveTile(index){
  if(!tInterval) startTimer();
  const emptyIdx=getEmptyIndex();
  [tiles[index],tiles[emptyIdx]]=[tiles[emptyIdx],tiles[index]];
  moves++;
  document.getElementById('m').textContent=moves;
  render();
}

// 计时器
function startTimer(){
  tInterval=setInterval(()=>{
    timer++;
    const m=Math.floor(timer/60).toString().padStart(2,'0');
    const s=(timer%60).toString().padStart(2,'0');
    document.getElementById('t').textContent=`${m}:${s}`;
  },1000);
}

function stopTimer(){
  clearInterval(tInterval);
}

// ✅ 还原：正方形裁剪 → 分9份 → 编号1-8 → 9号空格（可移动）
async function resetPuzzle(){
  tiles=[1,2,3,4,5,6,7,8,9];
  moves=0;
  timer=0;
  stopTimer();
  document.getElementById('m').textContent='0';
  document.getElementById('t').textContent='00:00';
  squareImg=await cropToSquare(imgList[currentImg]);
  render();
}

// 打乱拼图（空格可移动）
function shufflePuzzle(){
  resetPuzzle().then(()=>{
    for(let i=0;i<100;i++){
      const emptyIdx=getEmptyIndex();
      const directions=[-1,1,-3,3];
      const validMoves=directions.filter(d=>{
        const newIdx=emptyIdx+d;
        if(newIdx<0||newIdx>=9) return false;
        if(emptyIdx%3===0&&d===-1) return false;
        if(emptyIdx%3===2&&d===1) return false;
        return true;
      });
      if(validMoves.length>0){
        const randMove=validMoves[Math.floor(Math.random()*validMoves.length)];
        [tiles[emptyIdx],tiles[emptyIdx+randMove]]=[tiles[emptyIdx+randMove],tiles[emptyIdx]];
      }
    }
    render();
  });
}

// 自动还原
async function autoSolve(){
  stopTimer();
  while(!checkWin()){
    const emptyIdx=getEmptyIndex();
    for(let i=0;i<N2;i++){
      if(tiles[i]!==i+1){
        const ex=Math.floor(emptyIdx/3), ey=emptyIdx%3;
        const ix=Math.floor(i/3), iy=i%3;
        if(Math.abs(ex-ix)+Math.abs(ey-iy)===1){
          [tiles[i],tiles[emptyIdx]]=[tiles[emptyIdx],tiles[i]];
          moves++;
          document.getElementById('m').textContent=moves;
          render();
          await new Promise(r=>setTimeout(r,200));
          break;
        }
      }
    }
  }
}

// 初始化
(async ()=>{
  await resetPuzzle();
})();
</script>
</body>
</html>
'''

# 注入图片列表
image_list_str = '["' + '", "'.join(image_base64_list) + '"]'
puzzle_html = puzzle_html.replace('IMAGE_LIST_PLACEHOLDER', image_list_str)

components.html(puzzle_html, height=750)

st.write("---")
st.write("💡 游戏规则：点击与空格相邻的方块移动，将数字1-8按顺序拼好即可！")