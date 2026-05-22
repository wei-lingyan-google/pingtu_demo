# app.py
import streamlit as st
import streamlit.components.v1 as components
import os
import base64

st.title("🧩 拼图游戏")
st.write("✅ 点击空格相邻的方块移动，将图片恢复完整！")

# 获取图片列表并转换为 base64
image_files = [f for f in os.listdir('images') if f.endswith(('.jpg', '.jpeg', '.png'))]
image_files.sort()

# 将图片转换为 base64
image_base64_list = []
for img_file in image_files:
    img_path = os.path.join('images', img_file)
    try:
        with open(img_path, 'rb') as f:
            img_data = f.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            ext = img_file.split('.')[-1].lower()
            if ext == 'jpg' or ext == 'jpeg':
                image_base64_list.append(f'data:image/jpeg;base64,{img_base64}')
            else:
                image_base64_list.append(f'data:image/png;base64,{img_base64}')
    except Exception as e:
        st.error(f"无法加载图片 {img_file}: {e}")

# 如果没有图片，使用默认图片
if not image_base64_list:
    image_base64_list = [
        'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20cat%20portrait%20adorable&image_size=square'
    ]

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
        .puzzle-container { background: white; border-radius: 10px; padding: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 350px; margin: 0 auto; }
        .puzzle-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 3px; aspect-ratio: 1; background: #333; border-radius: 6px; padding: 3px; }
        .tile { background: #4ECDC4; background-size: 300% 300%; border-radius: 4px; cursor: pointer; transition: all 0.15s ease; }
        .tile:hover { transform: scale(1.02); }
        .tile.empty { background: #333 !important; cursor: default; }
        .tile.has-image { }
        .win-popup { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 25px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); text-align: center; z-index: 1000; }
        .win-popup.show { display: block; }
        .overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 999; }
        .overlay.show { display: block; }
        .win-popup button { margin-top: 15px; padding: 10px 25px; background: #4CAF50; color: white; border: none; border-radius: 6px; cursor: pointer; }
        .leaderboard { margin-top: 20px; padding: 15px; background: white; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 350px; margin-left: auto; margin-right: auto; }
        .leaderboard h3 { text-align: center; margin-bottom: 10px; color: #333; }
        .leaderboard table { width: 100%; border-collapse: collapse; }
        .leaderboard th, .leaderboard td { padding: 8px; text-align: center; border-bottom: 1px solid #eee; }
        .leaderboard th { background: #f8f9fa; }
        .leaderboard tr:last-child td { border-bottom: none; }
    </style>
</head>
<body>
    <div class="header">
        <button onclick="changeImage()">换图</button>
        <button onclick="newGame()">新游戏</button>
        <button onclick="resetPuzzle()">还原</button>
    </div>
    <div class="stats">
        <span>⏱️ 时间: <span id="timer">00:00</span></span>
        <span style="margin-left: 20px;">👣 步数: <span id="moves">0</span></span>
    </div>
    <div class="puzzle-container">
        <div class="puzzle-grid" id="puzzleGrid"></div>
    </div>
    
    <div class="leaderboard">
        <h3>🏆 排行榜</h3>
        <table>
            <thead>
                <tr><th>排名</th><th>用时</th><th>步数</th></tr>
            </thead>
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
        let puzzleSize = 3;
        let tiles = [];
        let moves = 0;
        let timer = 0;
        let timerInterval = null;
        let isPlaying = false;
        let currentCroppedUrl = '';
        
        const images = IMAGE_LIST_PLACEHOLDER;
        let currentImageIndex = 0;
        
        function loadAndCropImage(imageUrl) {
            return new Promise(function(resolve, reject) {
                const img = new Image();
                img.onload = function() {
                    const width = img.width;
                    const height = img.height;
                    let cropWidth = width;
                    let cropHeight = width;
                    let offsetX = 0;
                    let offsetY = 0;
                    
                    if (height > width) {
                        offsetY = (height - width) / 2;
                        cropHeight = width;
                    } else if (width > height) {
                        cropWidth = height;
                        offsetX = (width - height) / 2;
                    }
                    
                    const canvas = document.createElement('canvas');
                    canvas.width = cropWidth;
                    canvas.height = cropHeight;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, offsetX, offsetY, cropWidth, cropHeight, 0, 0, cropWidth, cropHeight);
                    resolve(canvas.toDataURL('image/jpeg', 0.95));
                };
                img.onerror = function() {
                    const canvas = document.createElement('canvas');
                    canvas.width = 300;
                    canvas.height = 300;
                    const ctx = canvas.getContext('2d');
                    ctx.fillStyle = '#4ECDC4';
                    ctx.fillRect(0, 0, 300, 300);
                    ctx.fillStyle = 'white';
                    ctx.font = '18px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText('图片加载失败', 150, 150);
                    resolve(canvas.toDataURL('image/png'));
                };
                img.src = imageUrl;
            });
        }
        
        async function initPuzzle() {
            stopTimer();
            moves = 0;
            timer = 0;
            isPlaying = false;
            document.getElementById('moves').textContent = '0';
            document.getElementById('timer').textContent = '00:00';
            
            const grid = document.getElementById('puzzleGrid');
            grid.innerHTML = '';
            tiles = [];
            
            try {
                currentCroppedUrl = await loadAndCropImage(images[currentImageIndex]);
                
                const totalTiles = puzzleSize * puzzleSize - 1;
                const positions = [];
                for (let i = 0; i < puzzleSize; i++) {
                    for (let j = 0; j < puzzleSize; j++) {
                        if (!(i === puzzleSize - 1 && j === puzzleSize - 1)) {
                            positions.push({ row: i, col: j });
                        }
                    }
                }
                
                shuffleArray(positions);
                while (!isSolvableWithEmpty(positions)) {
                    shuffleArray(positions);
                }
                
                let tileIndex = 0;
                for (let i = 0; i < puzzleSize; i++) {
                    for (let j = 0; j < puzzleSize; j++) {
                        if (i === puzzleSize - 1 && j === puzzleSize - 1) {
                            const emptyTile = document.createElement('div');
                            emptyTile.className = 'tile empty';
                            grid.appendChild(emptyTile);
                        } else {
                            const pos = positions[tileIndex];
                            const tile = document.createElement('div');
                            tile.className = 'tile has-image';
                            tile.dataset.originalRow = Math.floor(tileIndex / puzzleSize);
                            tile.dataset.originalCol = tileIndex % puzzleSize;
                            tile.dataset.currentRow = pos.row;
                            tile.dataset.currentCol = pos.col;
                            
                            const bgX = (tileIndex % puzzleSize) * 100;
                            const bgY = Math.floor(tileIndex / puzzleSize) * 100;
                            tile.style.backgroundImage = 'url(' + currentCroppedUrl + ')';
                            tile.style.backgroundPosition = bgX + '% ' + bgY + '%';
                            
                            tile.addEventListener('click', function() { onTileClick(tile); });
                            tiles.push(tile);
                            grid.appendChild(tile);
                            tileIndex++;
                        }
                    }
                }
            } catch (error) {
                console.error('Error:', error);
            }
            
            loadLeaderboard();
        }
        
        function shuffleArray(array) {
            for (let i = array.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }
        }
        
        function isSolvableWithEmpty(positions) {
            let inversions = 0;
            const flatPositions = positions.map(function(p) { return p.row * puzzleSize + p.col; });
            for (let i = 0; i < flatPositions.length; i++) {
                for (let j = i + 1; j < flatPositions.length; j++) {
                    if (flatPositions[i] > flatPositions[j]) inversions++;
                }
            }
            return inversions % 2 === 0;
        }
        
        function onTileClick(tile) {
            if (!isPlaying) { 
                startTimer(); 
                isPlaying = true; 
            }
            
            const row = parseInt(tile.dataset.currentRow);
            const col = parseInt(tile.dataset.currentCol);
            const grid = document.getElementById('puzzleGrid');
            const gridItems = grid.children;
            
            let emptyItem = null;
            let emptyPos = null;
            for (let i = 0; i < gridItems.length; i++) {
                const item = gridItems[i];
                if (item.classList.contains('empty')) {
                    const ir = Math.floor(i / puzzleSize);
                    const ic = i % puzzleSize;
                    if ((Math.abs(ir - row) === 1 && ic === col) || (Math.abs(ic - col) === 1 && ir === row)) {
                        emptyItem = item;
                        emptyPos = { row: ir, col: ic, index: i };
                        break;
                    }
                }
            }
            
            if (emptyPos && emptyItem) {
                const tileIndex = row * puzzleSize + col;
                tile.dataset.currentRow = emptyPos.row;
                tile.dataset.currentCol = emptyPos.col;
                
                const tileRef = tile;
                const emptyRef = emptyItem;
                const tileNextSibling = tileRef.nextSibling;
                
                grid.insertBefore(emptyRef, tileRef);
                if (tileNextSibling) {
                    grid.insertBefore(tileRef, tileNextSibling);
                } else {
                    grid.appendChild(tileRef);
                }
                
                moves++;
                document.getElementById('moves').textContent = moves;
                
                if (checkWin()) {
                    stopTimer();
                    saveScore();
                    showWinPopup();
                }
            }
        }
        
        function checkWin() {
            return tiles.every(function(tile) {
                return tile.dataset.originalRow === tile.dataset.currentRow &&
                       tile.dataset.originalCol === tile.dataset.currentCol;
            });
        }
        
        function startTimer() {
            timerInterval = setInterval(function() {
                timer++;
                const minutes = Math.floor(timer / 60);
                const seconds = timer % 60;
                document.getElementById('timer').textContent = minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0');
            }, 1000);
        }
        
        function stopTimer() {
            if (timerInterval) { 
                clearInterval(timerInterval); 
                timerInterval = null; 
            }
        }
        
        function showWinPopup() {
            document.getElementById('finalTime').textContent = Math.floor(timer / 60).toString().padStart(2, '0') + ':' + (timer % 60).toString().padStart(2, '0');
            document.getElementById('finalMoves').textContent = moves;
            document.getElementById('overlay').classList.add('show');
            document.getElementById('winPopup').classList.add('show');
        }
        
        function closeWinPopup() {
            document.getElementById('overlay').classList.remove('show');
            document.getElementById('winPopup').classList.remove('show');
            newGame();
        }
        
        function newGame() {
            initPuzzle();
        }
        
        function resetPuzzle() {
            stopTimer();
            moves = 0;
            timer = 0;
            isPlaying = false;
            document.getElementById('moves').textContent = '0';
            document.getElementById('timer').textContent = '00:00';
            
            const grid = document.getElementById('puzzleGrid');
            grid.innerHTML = '';
            tiles = [];
            
            try {
                const totalTiles = puzzleSize * puzzleSize - 1;
                const positions = [];
                for (let i = 0; i < puzzleSize; i++) {
                    for (let j = 0; j < puzzleSize; j++) {
                        if (!(i === puzzleSize - 1 && j === puzzleSize - 1)) {
                            positions.push({ row: i, col: j });
                        }
                    }
                }
                
                shuffleArray(positions);
                while (!isSolvableWithEmpty(positions)) {
                    shuffleArray(positions);
                }
                
                let tileIndex = 0;
                for (let i = 0; i < puzzleSize; i++) {
                    for (let j = 0; j < puzzleSize; j++) {
                        if (i === puzzleSize - 1 && j === puzzleSize - 1) {
                            const emptyTile = document.createElement('div');
                            emptyTile.className = 'tile empty';
                            grid.appendChild(emptyTile);
                        } else {
                            const pos = positions[tileIndex];
                            const tile = document.createElement('div');
                            tile.className = 'tile has-image';
                            tile.dataset.originalRow = Math.floor(tileIndex / puzzleSize);
                            tile.dataset.originalCol = tileIndex % puzzleSize;
                            tile.dataset.currentRow = pos.row;
                            tile.dataset.currentCol = pos.col;
                            
                            const bgX = (tileIndex % puzzleSize) * 100;
                            const bgY = Math.floor(tileIndex / puzzleSize) * 100;
                            tile.style.backgroundImage = 'url(' + currentCroppedUrl + ')';
                            tile.style.backgroundPosition = bgX + '% ' + bgY + '%';
                            
                            tile.addEventListener('click', function() { onTileClick(tile); });
                            tiles.push(tile);
                            grid.appendChild(tile);
                            tileIndex++;
                        }
                    }
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        function changeImage() {
            currentImageIndex = (currentImageIndex + 1) % images.length;
            initPuzzle();
        }
        
        function saveScore() {
            const scores = JSON.parse(localStorage.getItem('puzzleScores') || '[]');
            scores.push({ time: timer, moves: moves, date: new Date().toISOString() });
            scores.sort(function(a, b) {
                if (a.time !== b.time) return a.time - b.time;
                return a.moves - b.moves;
            });
            localStorage.setItem('puzzleScores', JSON.stringify(scores.slice(0, 10)));
            loadLeaderboard();
        }
        
        function loadLeaderboard() {
            const scores = JSON.parse(localStorage.getItem('puzzleScores') || '[]');
            const tbody = document.getElementById('leaderboardBody');
            tbody.innerHTML = '';
            
            if (scores.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" style="color: #999;">暂无记录</td></tr>';
                return;
            }
            
            scores.forEach(function(score, index) {
                const tr = document.createElement('tr');
                const rank = index + 1;
                const time = Math.floor(score.time / 60).toString().padStart(2, '0') + ':' + (score.time % 60).toString().padStart(2, '0');
                let rankIcon = rank;
                if (rank === 1) rankIcon = '🥇';
                else if (rank === 2) rankIcon = '🥈';
                else if (rank === 3) rankIcon = '🥉';
                tr.innerHTML = '<td>' + rankIcon + '</td><td>' + time + '</td><td>' + score.moves + '</td>';
                tbody.appendChild(tr);
            });
        }
        
        initPuzzle();
    </script>
</body>
</html>
"""

# 替换图片列表占位符
image_list_str = '["' + '", "'.join(image_base64_list) + '"]'
puzzle_html = puzzle_html.replace('IMAGE_LIST_PLACEHOLDER', image_list_str)

# 显示图片列表供确认
st.write(f"📷 已加载 {len(image_base64_list)} 张图片")

# 嵌入拼图游戏
components.html(puzzle_html, height=700)

st.write("---")
st.write("💡 **游戏说明**：点击空格相邻的方块，将图片恢复完整！")