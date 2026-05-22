# app.py
import streamlit as st
import streamlit.components.v1 as components

st.title("🧩 拼图游戏")
st.write("✅ 点击空格相邻的方块移动，将图片恢复完整！")

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
        .tile { background: #fff; background-size: 300% 300%; border-radius: 4px; cursor: pointer; transition: all 0.15s ease; }
        .tile:hover { transform: scale(1.02); }
        .tile.empty { background: #333 !important; cursor: default; }
        .win-popup { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 25px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); text-align: center; z-index: 1000; }
        .win-popup.show { display: block; }
        .overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 999; }
        .overlay.show { display: block; }
        .win-popup button { margin-top: 15px; padding: 10px 25px; background: #4CAF50; color: white; border: none; border-radius: 6px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <button onclick="changeImage()">换图</button>
        <button onclick="newGame()">新游戏</button>
    </div>
    <div class="stats">
        <span>⏱️ 时间: <span id="timer">00:00</span></span>
        <span style="margin-left: 20px;">👣 步数: <span id="moves">0</span></span>
    </div>
    <div class="puzzle-container">
        <div class="puzzle-grid" id="puzzleGrid"></div>
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
        
        const images = [
            'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20cat%20portrait%20adorable&image_size=square',
            'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=beautiful%20sunset%20mountain%20landscape&image_size=square',
            'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=colorful%20flowers%20garden%20spring&image_size=square',
            'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=ocean%20beach%20tropical%20paradise&image_size=square',
            'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20puppy%20dog%20adorable&image_size=square'
        ];
        let currentImageIndex = 0;
        
        function loadAndCropImage(imageUrl) {
            return new Promise((resolve, reject) => {
                const img = new Image();
                img.crossOrigin = 'anonymous';
                img.onload = () => {
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
                img.onerror = () => {
                    const canvas = document.createElement('canvas');
                    canvas.width = 300;
                    canvas.height = 300;
                    const ctx = canvas.getContext('2d');
                    ctx.fillStyle = '#4ECDC4';
                    ctx.fillRect(0, 0, 300, 300);
                    ctx.fillStyle = 'white';
                    ctx.font = '18px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText('图片加载中...', 150, 150);
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
                const croppedUrl = await loadAndCropImage(images[currentImageIndex]);
                
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
                            tile.className = 'tile';
                            tile.dataset.originalRow = Math.floor(tileIndex / puzzleSize);
                            tile.dataset.originalCol = tileIndex % puzzleSize;
                            tile.dataset.currentRow = pos.row;
                            tile.dataset.currentCol = pos.col;
                            
                            const bgX = (tileIndex % puzzleSize) * 100;
                            const bgY = Math.floor(tileIndex / puzzleSize) * 100;
                            tile.style.backgroundImage = `url(${croppedUrl})`;
                            tile.style.backgroundPosition = `${bgX}% ${bgY}%`;
                            
                            tile.addEventListener('click', () => onTileClick(tile));
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
        
        function shuffleArray(array) {
            for (let i = array.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }
        }
        
        function isSolvableWithEmpty(positions) {
            let inversions = 0;
            const flatPositions = positions.map(p => p.row * puzzleSize + p.col);
            for (let i = 0; i < flatPositions.length; i++) {
                for (let j = i + 1; j < flatPositions.length; j++) {
                    if (flatPositions[i] > flatPositions[j]) inversions++;
                }
            }
            return inversions % 2 === 0;
        }
        
        function onTileClick(tile) {
            if (!isPlaying) { startTimer(); isPlaying = true; }
            
            const row = parseInt(tile.dataset.currentRow);
            const col = parseInt(tile.dataset.currentCol);
            const grid = document.getElementById('puzzleGrid');
            const gridItems = grid.children;
            
            let emptyPos = null;
            for (let i = 0; i < gridItems.length; i++) {
                const item = gridItems[i];
                if (item.classList.contains('empty')) {
                    const ir = Math.floor(i / puzzleSize);
                    const ic = i % puzzleSize;
                    if ((Math.abs(ir - row) === 1 && ic === col) || (Math.abs(ic - col) === 1 && ir === row)) {
                        emptyPos = { row: ir, col: ic, index: i };
                        break;
                    }
                }
            }
            
            if (emptyPos) {
                const tileIndex = row * puzzleSize + col;
                tile.dataset.currentRow = emptyPos.row;
                tile.dataset.currentCol = emptyPos.col;
                
                grid.removeChild(tile);
                grid.insertBefore(tile, grid.children[emptyPos.index]);
                
                moves++;
                document.getElementById('moves').textContent = moves;
                
                if (checkWin()) {
                    stopTimer();
                    showWinPopup();
                }
            }
        }
        
        function checkWin() {
            return tiles.every(tile => 
                tile.dataset.originalRow === tile.dataset.currentRow &&
                tile.dataset.originalCol === tile.dataset.currentCol
            );
        }
        
        function startTimer() {
            timerInterval = setInterval(() => {
                timer++;
                const minutes = Math.floor(timer / 60);
                const seconds = timer % 60;
                document.getElementById('timer').textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }, 1000);
        }
        
        function stopTimer() {
            if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
        }
        
        function showWinPopup() {
            document.getElementById('finalTime').textContent = `${Math.floor(timer / 60).toString().padStart(2, '0')}:${(timer % 60).toString().padStart(2, '0')}`;
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
        
        function changeImage() {
            currentImageIndex = (currentImageIndex + 1) % images.length;
            initPuzzle();
        }
        
        initPuzzle();
    </script>
</body>
</html>
"""

# 嵌入拼图游戏
components.html(puzzle_html, height=500)

st.write("---")
st.write("💡 **游戏说明**：点击空格相邻的方块，将图片恢复完整！")