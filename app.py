# app.py
import streamlit as st
import streamlit.components.v1 as components
import os
import base64

st.title("🧩 钧崽变变变")
st.write("✅ 点击空格相邻的方块移动，将图片恢复完整！")

# 获取图片列表并转换为 base64
image_files = [f for f in os.listdir('images') if f.endswith(('.jpg', '.jpeg', '.png'))]
image_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else 0)

# 将图片转换为 base64
image_base64_list = []
for img_file in image_files:
    img_path = os.path.join('images', img_file)
    try:
        with open(img_path, 'rb') as f:
            img_data = f.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            ext = img_file.split('.')[-1].lower()
            mime = 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
            image_base64_list.append(f'data:{mime};base64,{img_base64}')
    except Exception as e:
        st.error(f"无法加载图片 {img_file}: {e}")

# 默认图片
if not image_base64_list:
    image_base64_list = ['https://picsum.photos/300/300']

# 拼图游戏 HTML 代码
puzzle_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Microsoft YaHei', sans-serif; background: #f0f0f0; padding: 10px; }
        .header { display: flex; justify-content: center; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; }
        .header button { padding: 8px 16px; font-size: 14px; border: none; border-radius: 6px; background: #667eea; color: white; cursor: pointer; }
        .header button:hover { background: #5a6fd6; }
        .stats { text-align: center; margin-bottom: 10px; font-weight: bold; }
        /* 原图展示区域 */
        .original-image { 
            max-width: 350px; 
            margin: 0 auto 15px; 
            display: none; /* 默认隐藏 */
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .original-image img { width: 100%; display: block; }
        .puzzle-container { background: white; border-radius: 10px; padding: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 350px; margin: 0 auto; }
        .puzzle-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 3px; aspect-ratio: 1; background: #333; border-radius: 6px; padding: 3px; }
        .tile { 
            background: #4ECDC4; 
            background-size: 300% 300%; 
            border-radius: 4px; 
            transition: all 0.15s ease; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            font-size: 26px;
            font-weight: bold;
            color: white;
            text-shadow: 0 0 5px rgba(0,0,0,0.8);
        }
        .tile.empty { 
            background: #333 !important; 
            cursor: default;
            color: transparent;
        }
        .tile.has-image { cursor: pointer; }
        .tile.movable { cursor: pointer; box-shadow: 0 0 10px rgba(78, 205, 196, 0.8); }
        .tile.movable:hover { transform: scale(1.02); }
        .win-popup { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 25px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); text-align: center; z-index: 1000; }
        .win-popup.show { display: block; }
        .overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 999; }
        .overlay.show { display: block; }
        .win-popup button { margin-top: 15px; padding: 10px 25px; background: #4CAF50; color: white; border: none; border-radius: 6px; cursor: pointer; }
        .leaderboard { margin-top: 20px; padding: 15px; background: white; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 350px; margin: 20px auto; }
        .leaderboard h3 { text-align: center; margin-bottom: 10px; color: #333; }
        .leaderboard table { width: 100%; border-collapse: collapse; }
        .leaderboard th, .leaderboard td { padding: 8px; text-align: center; border-bottom: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="header">
        <button onclick="autoSolve()">自动还原</button>
        <button onclick="newGame()">新游戏</button>
        <button onclick="resetPuzzle()">还原</button>
    </div>
    <div class="stats">
        <span>⏱️ 时间: <span id="timer">00:00</span></span>
        <span style="margin-left: 20px;">👣 步数: <span id="moves">0</span></span>
    </div>

    <!-- 原图展示区域 -->
    <div class="original-image" id="originalImage">
        <img id="originalImg" src="" alt="原图">
    </div>

    <div class="puzzle-container">
        <div class="puzzle-grid" id="puzzleGrid"></div>
    </div>
    
    <div class="leaderboard">
        <h3>🏆 排行榜</h3>
        <table>
            <thead><tr><th>排名</th><th>用时</th><th>步数</th></tr></thead>
            <tbody id="leaderboardBody"></tbody>
        </table>
    </div>
    
    <div class="overlay" id="overlay"></div>
    <div class="win-popup" id="winPopup">
        <h2>🎉 恭喜完成！</h2>
        <p>用时: <span id="finalTime">00:00</span></p>
        <p>步数: <span id="finalMoves">0</span></p>
        <button onclick="closeWinPopup()">再来一局</button>
    </div>

    <script>
        const N = 3;
        const N2 = 9;
        const dx = [0, 0, -1, 1];
        const dy = [-1, 1, 0, 0];
        const pth = ['u', 'd', 'l', 'r'];
        
        let currentImageIndex = 0;
        let currentCroppedUrl = '';
        let moves = 0;
        let timer = 0;
        let timerInterval = null;
        let isPlaying = false;
        let isAutoSolving = false;
        
        const images = IMAGE_LIST_PLACEHOLDER;
        let tiles = [];
        // 核心：空格永久固定在右下角（索引8）
        const SPACE_INDEX = 8;

        // 加载裁剪图片
        function loadAndCropImage(imageUrl) {
            return new Promise((resolve) => {
                const img = new Image();
                img.onload = () => {
                    const size = Math.min(img.width, img.height);
                    const canvas = document.createElement('canvas');
                    canvas.width = canvas.height = size;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, (img.width-size)/2, (img.height-size)/2, size, size, 0, 0, size, size);
                    resolve(canvas.toDataURL('image/jpeg'));
                };
                img.onerror = () => resolve('https://picsum.photos/300/300');
                img.src = imageUrl;
            });
        }

        // 初始化正确拼图：1-8顺序，右下角空格（基准拼图）
        function initCorrectTiles() {
            tiles = [0,1,2,3,4,5,6,7,8];
            // 还原时显示原图
            document.getElementById('originalImage').style.display = 'block';
            document.getElementById('originalImg').src = images[currentImageIndex];
        }

        // 核心：基于正确拼图打乱，仅打乱前8块，空格固定最后
        function initShuffledTiles() {
            tiles = [0,1,2,3,4,5,6,7];
            // 随机打乱前8个拼图块
            for (let i = tiles.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [tiles[i], tiles[j]] = [tiles[j], tiles[i]];
            }
            // 强制最后一位为空格，绝不修改
            tiles.push(8);
            // 打乱时隐藏原图
            document.getElementById('originalImage').style.display = 'none';
        }

        // 判断是否完成拼图
        function isTarget() {
            for (let i = 0; i < N2; i++) {
                if (tiles[i] !== i) return false;
            }
            return true;
        }

        // 判断方块是否可移动
        function isMovable(index) {
            const sx = Math.floor(SPACE_INDEX / N);
            const sy = SPACE_INDEX % N;
            const tx = Math.floor(index / N);
            const ty = index % N;
            return Math.abs(sx - tx) + Math.abs(sy - ty) === 1;
        }

        // 渲染拼图网格
        function renderGrid() {
            const grid = document.getElementById('puzzleGrid');
            grid.innerHTML = '';
            for (let i = 0; i < N2; i++) {
                const val = tiles[i];
                const tile = document.createElement('div');
                
                if (i === SPACE_INDEX) {
                    tile.className = 'tile empty';
                } else {
                    tile.className = 'tile has-image';
                    tile.textContent = val + 1; // 显示编号1-8
                    if (isMovable(i)) tile.classList.add('movable');
                    
                    const col = val % N;
                    const row = Math.floor(val / N);
                    tile.style.backgroundImage = `url(${currentCroppedUrl})`;
                    tile.style.backgroundPosition = `${col * 100}% ${row * 100}%`;
                    tile.onclick = () => onTileClick(i);
                }
                grid.appendChild(tile);
            }
        }

        // 点击方块移动
        function onTileClick(index) {
            if (!isMovable(index) || isAutoSolving) return;
            if (!isPlaying) { startTimer(); isPlaying = true; }
            
            // 交换点击的方块和空格
            [tiles[index], tiles[SPACE_INDEX]] = [tiles[SPACE_INDEX], tiles[index]];
            moves++;
            document.getElementById('moves').textContent = moves;
            
            renderGrid();
            if (isTarget()) { stopTimer(); saveScore(); showWinPopup(); }
        }

        // 自动解谜
        async function autoSolve() {
            if (isAutoSolving) return;
            isAutoSolving = true;
            stopTimer();
            
            // 还原到基准拼图
            while (!isTarget()) {
                for (let i = 0; i < N2-1; i++) {
                    if (tiles[i] !== i && isMovable(i)) {
                        [tiles[i], tiles[SPACE_INDEX]] = [tiles[SPACE_INDEX], tiles[i]];
                        moves++;
                        document.getElementById('moves').textContent = moves;
                        renderGrid();
                        await new Promise(r => setTimeout(r, 200));
                        break;
                    }
                }
            }
            
            isAutoSolving = false;
            saveScore();
            showWinPopup();
        }

        // 计时器
        function startTimer() {
            timerInterval = setInterval(() => {
                timer++;
                const m = Math.floor(timer/60).toString().padStart(2,'0');
                const s = (timer%60).toString().padStart(2,'0');
                document.getElementById('timer').textContent = `${m}:${s}`;
            }, 1000);
        }

        function stopTimer() { clearInterval(timerInterval); }

        // 游戏控制
        function resetGameStats() {
            stopTimer();
            moves = timer = 0;
            isPlaying = false;
            document.getElementById('moves').textContent = '0';
            document.getElementById('timer').textContent = '00:00';
        }

        async function initPuzzle() {
            currentCroppedUrl = await loadAndCropImage(images[currentImageIndex]);
            initShuffledTiles();
            renderGrid();
            loadLeaderboard();
        }

        // 新游戏：打乱拼图，隐藏原图
        function newGame() { 
            initShuffledTiles(); 
            renderGrid(); 
            resetGameStats(); 
        }

        // 还原：恢复基准拼图，显示完整原图
        function resetPuzzle() { 
            initCorrectTiles(); 
            renderGrid(); 
            resetGameStats(); 
        }

        // 弹窗与排行榜
        function showWinPopup() {
            const m = Math.floor(timer/60).toString().padStart(2,'0');
            const s = (timer%60).toString().padStart(2,'0');
            document.getElementById('finalTime').textContent = `${m}:${s}`;
            document.getElementById('finalMoves').textContent = moves;
            document.getElementById('overlay').classList.add('show');
            document.getElementById('winPopup').classList.add('show');
        }

        function closeWinPopup() {
            document.getElementById('overlay').classList.remove('show');
            document.getElementById('winPopup').classList.remove('show');
            newGame();
        }

        function saveScore() {
            let scores = JSON.parse(localStorage.getItem('puzzleScores')||'[]');
            scores.push({time:timer, moves:moves});
            scores.sort((a,b)=>a.time-b.time||a.moves-b.moves);
            localStorage.setItem('puzzleScores', JSON.stringify(scores.slice(0,10)));
            loadLeaderboard();
        }

        function loadLeaderboard() {
            const scores = JSON.parse(localStorage.getItem('puzzleScores')||'[]');
            const tbody = document.getElementById('leaderboardBody');
            tbody.innerHTML = scores.length ? scores.map((s,i)=>{
                const t = `${Math.floor(s.time/60).toString().padStart(2,'0')}:${(s.time%60).toString().padStart(2,'0')}`;
                const r = i+1;
                const icon = r===1?'🥇':r===2?'🥈':r===3?'🥉':r;
                return `<tr><td>${icon}</td><td>${t}</td><td>${s.moves}</td></tr>`;
            }).join('') : '<tr><td colspan="3">暂无记录</td></tr>';
        }

        // 启动游戏
        initPuzzle();
    </script>
</body>
</html>
"""

# 替换图片列表
image_list_str = '["' + '", "'.join(image_base64_list) + '"]'
puzzle_html = puzzle_html.replace('IMAGE_LIST_PLACEHOLDER', image_list_str)

st.write(f"📷 已加载 {len(image_base64_list)} 张图片")
components.html(puzzle_html, height=800)

st.write("---")
st.write("💡 **游戏说明**：点击空格相邻的方块移动，将图片恢复完整！")