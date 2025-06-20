<template>
    <div class="floor-map-container">
        <div class="controls">
            <div class="search-box">
                <input v-model="searchKeyword" type="text" placeholder="输入区域名称或人员" @input="handleSearch">
            </div>
            <button class="draw-btn" @click="toggleDrawingMode" :class="{ active: isDrawingMode }">
                {{ isDrawingMode ? '完成绘制' : '开始绘制' }}
            </button>
            <button class="erase-draw-btn" v-if="drawingPoints.length > 0" @click="clearDrawing">清除绘制</button>
            <button class="show-all-btn" @click="seeAllAreas">查看全部区域</button>
        </div>
        <canvas ref="canvas" @mousemove="handleMouseMove" @mouseout="handleMouseOut"
            @contextmenu.prevent="handleRightClick" @click="handleCanvasClick"></canvas>
        <!-- 信息卡 -->
        <div v-if="hoveredArea" class="tooltip" :style="{
            position: 'fixed' as const,
            left: `${mousePosition.x + 10}px`,
            top: `${mousePosition.y - 30}px`
        }">
            <p v-if="hoveredArea.name" style="text-align: center;">{{ hoveredArea.name }}</p>
            <p v-if="hoveredArea.teachers!?.length > 0">人员：{{ hoveredArea.teachers?.join(', ') }}</p>
            <p v-if="hoveredArea.info">{{ hoveredArea.info }}</p>
        </div>
        <div v-if="flashingArea" class="tooltip flashing-area">
            <p v-if="flashingArea.name" style="text-align: center;">{{ flashingArea.name }}</p>
            <p v-if="flashingArea.teachers!?.length > 0">人员：{{ flashingArea.teachers?.join(', ') }}</p>
            <p v-if="flashingArea.info">{{ flashingArea.info }}</p>
        </div>
    </div>

    <!-- 新建区域弹窗 -->
    <div v-if="showAreaDialog" class="area-dialog">
        <div class="dialog-content">
            <h3>新建区域</h3>
            <div class="form-group">
                <label>区域名：</label>
                <input v-model="newArea.name" type="text" placeholder="请输入区域名">
            </div>
            <div class="form-group">
                <label>区域颜色：</label>
                <input v-model="newArea.color" type="color">
            </div>
            <div class="form-group">
                <label>区域信息：</label>
                <textarea v-model="newArea.info" placeholder="请输入区域信息"></textarea>
            </div>
            <div class="form-group">
                <label style="display: flex;">人员：<span @click="addTeacher">+</span></label>
                <div v-for="(_, index) in newArea.teachers" :key="index" class="teacher-input">
                    <input v-model="newArea.teachers[index]" type="text" placeholder="请输入姓名">
                    <button @click="removeTeacher(index)" class="remove-btn">删除</button>
                </div>
            </div>
            <div class="dialog-buttons">
                <button @click="confirmArea" class="confirm-btn">确认</button>
                <button @click="cancelArea" class="cancel-btn">取消</button>
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup name='InteractiveFloorMap'>
import { ref, onMounted, onUnmounted } from 'vue';
import request from '../api/request';

interface MapArea {
    id: number;
    name: string;
    path: Path2D;
    color: string;
    hoverColor: string;
    coordinates: number[][];
    info?: string;
    teachers?: string[];
}

onMounted(() => {
    initCanvas();
});

const seeAllAreas = () => {
    alert(" 请打开F12 Console查看");
    console.log(areas.value);
}

const bgImage = new Image();
bgImage.src = new URL('../assets/jishi4.jpg', import.meta.url).href;

const canvas = ref<HTMLCanvasElement | null>(null);
const ctx = ref<CanvasRenderingContext2D | null>(null);
const hoveredArea = ref<MapArea | null>(null);
const areas = ref<MapArea[]>([]);

// 初始化Canvas
const initCanvas = () => {
    if (!canvas.value) return;

    ctx.value = canvas.value.getContext('2d');
    if (!ctx.value) return;

    // 设置Canvas大小
    canvas.value.width = 2265 / 2.5; // 根据图片调整
    canvas.value.height = 2767 / 2.5; // 根据图片调整

    // 绘制地图和区域
    drawMap();
};

// 绘制地图和定义交互区域
const drawMap = () => {
    if (!ctx.value || !canvas.value) return;
    bgImage.onload = () => {
        // 清除画布
        ctx.value!.clearRect(0, 0, canvas.value!.width, canvas.value!.height);
        // 绘制图片
        ctx.value!.drawImage(bgImage, 0, 0, canvas.value!.width, canvas.value!.height);
        // 定义交互区域
        getAreasAndDraw();
    };
};

const getAreasAndDraw = async () => {
    if (!ctx.value) return;
    try {
        const res = await request.get('/getAllAreas');
        if (res.data.status !== 200) return;
        const areasData = res.data.areas;
        areas.value = areasData.map((area: any) => ({
            path: new Path2D(area.svgPath),
            ...area
        }));
    } catch (error) {
        console.error('Error fetching areas:', error);
        return;
    }
    drawAreas();
};

const drawAreas = () => {
    if (!ctx.value || !canvas.value) return;
    // 重绘底图
    ctx.value.drawImage(bgImage, 0, 0, canvas.value.width, canvas.value.height);
    // 绘制所有已定义的区域
    areas.value.forEach(area => {
        ctx.value!.fillStyle = area === hoveredArea.value ? area.hoverColor : area.color;
        ctx.value!.fill(area.path);
        ctx.value!.strokeStyle = '#333';
        ctx.value!.lineWidth = 2;
        ctx.value!.stroke(area.path);
    });
    // 绘制正在绘制的临时路径
    if (tempPath.value && isDrawingMode.value) {
        ctx.value.strokeStyle = 'red';
        ctx.value.lineWidth = 2;
        ctx.value.stroke(tempPath.value);
    }
};


// 鼠标移动事件处理
const mousePosition = ref({ x: 0, y: 0 });

const handleMouseMove = (event: MouseEvent) => {
    if (!canvas.value || !ctx.value) return;

    const rect = canvas.value.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    // 定位鼠标位置
    mousePosition.value = {
        x: event.clientX,
        y: event.clientY
    };
    // 检查鼠标是否在某个区域内
    let newHoveredArea: MapArea | null = null;
    for (const area of areas.value) {
        if (ctx.value.isPointInPath(area.path, x, y)) {
            newHoveredArea = area;
            break;
        }
    }
    // 如果悬停区域发生变化，重新绘制
    if (newHoveredArea !== hoveredArea.value) {
        hoveredArea.value = newHoveredArea;
        drawAreas();
    }
};

// 鼠标移出事件处理
const handleMouseOut = () => {
    hoveredArea.value = null;
    drawAreas();
};

// 删除部分
// 处理右键点击事件
const handleRightClick = (event: MouseEvent) => {
    if (!canvas.value || !ctx.value) return;

    const rect = canvas.value.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // 检查鼠标是否在某个区域内
    for (const area of areas.value) {
        if (ctx.value.isPointInPath(area.path, x, y)) {
            if (confirm(`是否要删除区域：${area.name}?`)) {
                deleteArea(area);
            }
            break;
        }
    }
};

const deleteArea = async (area: MapArea) => {
    try {
        const res = await request.post('/deleteArea', {
            id: area.id
        });
        if (res.data.status !== 200) return;
        await getAreasAndDraw();
    } catch (error) {
        console.error('Error deleting area:', error);
    }
};

// 绘制部分
const showAreaDialog = ref(false);
const newArea = ref({
    name: '',
    color: '#64c8ff',
    info: '',
    teachers: [] as string[]
});

const isDrawingMode = ref(false);
const drawingPoints = ref<number[][]>([]);
const tempPath = ref<Path2D | null>(null);

// 切换绘制模式
const toggleDrawingMode = () => {
    if (isDrawingMode.value && drawingPoints.value.length >= 3) {
        showAreaDialog.value = true;
    } else {
        clearDrawing();
        isDrawingMode.value = !isDrawingMode.value;
    }
};

// 添加教师输入框
const addTeacher = () => {
    newArea.value.teachers.push('');
};
// 删除教师输入框
const removeTeacher = (index: number) => {
    newArea.value.teachers = newArea.value.teachers.filter((_, i) => i !== index);
};

// 创建新的交互区域
const addNewArea = async () => {
    const params = {
        name: newArea.value.name,
        color: `${newArea.value.color}4D`,
        hoverColor: `${newArea.value.color}99`,
        info: newArea.value.info,
        teachers: newArea.value.teachers,
        svgPath: `M${drawingPoints.value.map(point => point.join(',')).join(' L')} Z`,
        coordinates: drawingPoints.value
    };
    if (params.coordinates.length < 3) {
        alert('请至少绘制三个点来创建区域');
        return;
    }
    try {
        const res = await request.post('/addNewArea', params);
        if (res.data.status !== 200) return;
        await getAreasAndDraw();
    } catch (error) {
        console.error('Error adding area:', error);
    }
    drawAreas();
};

// 清除当前绘制
const clearDrawing = () => {
    drawingPoints.value = [];
    tempPath.value = null;
    drawAreas(); // 重绘所有区域
};

const confirmArea = async () => {
    if (!newArea.value.name) {
        alert('请输入区域名称');
        return;
    }

    await addNewArea();

    // 重置并关闭弹窗
    showAreaDialog.value = false;
    newArea.value = {
        name: '',
        color: '#64c8ff',
        info: '',
        teachers: [] as string[]
    };
    clearDrawing();
    isDrawingMode.value = false;
};

// 取消创建区域
const cancelArea = () => {
    showAreaDialog.value = false;
    clearDrawing();
    isDrawingMode.value = false;
};

// 修改 handleCanvasClick 方法
const handleCanvasClick = (event: MouseEvent) => {
    if (!canvas.value || !ctx.value) return;

    const rect = canvas.value.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    if (isDrawingMode.value) {
        // 在绘制模式下，记录点击的坐标
        drawingPoints.value.push([x, y]);

        // 绘制临时路径
        tempPath.value = new Path2D();
        tempPath.value.moveTo(drawingPoints.value[0][0], drawingPoints.value[0][1]);

        for (let i = 1; i < drawingPoints.value.length; i++) {
            tempPath.value.lineTo(drawingPoints.value[i][0], drawingPoints.value[i][1]);
        }

        // 如果有超过2个点，就闭合路径
        if (drawingPoints.value.length > 2) {
            tempPath.value.closePath();
        }

        // 重绘
        drawAreas();

        // 绘制临时路径
        if (tempPath.value) {
            ctx.value.strokeStyle = '#ff0000';
            ctx.value.lineWidth = 2;
            ctx.value.stroke(tempPath.value);
        }
    } else {
        // 非绘制模式下，处理区域点击
        if (hoveredArea.value) {
            console.log(`Clicked on: ${hoveredArea.value.name}`);
        }
    }
};

// 搜索部分
const searchKeyword = ref('');
const flashingArea = ref<MapArea | null>(null);
const flashInterval = ref<number | null>(null);

// 处理搜索
const handleSearch = () => {
    // 清除之前的闪烁效果
    if (flashInterval.value) {
        clearInterval(flashInterval.value);
        flashInterval.value = null;
    }
    flashingArea.value = null;

    if (!searchKeyword.value) {
        drawAreas();
        return;
    }

    // 查找匹配的区域
    const matchedArea = areas.value.find(area =>
        area.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
        area.teachers?.some(teacher => teacher.toLowerCase().includes(searchKeyword.value.toLowerCase())) ||
        area.info?.toLowerCase().includes(searchKeyword.value.toLowerCase())
    );

    if (matchedArea) {
        flashingArea.value = matchedArea;
        let isHighlighted = true;

        // 创建闪烁效果
        flashInterval.value = setInterval(() => {
            if (!ctx.value || !canvas.value) return;

            // 重绘所有区域
            drawAreas();

            // 绘制闪烁区域
            if (isHighlighted && flashingArea.value) {
                ctx.value.fillStyle = flashingArea.value.hoverColor;
                ctx.value.fill(flashingArea.value.path);
                ctx.value.strokeStyle = '#ff0000';
                ctx.value.lineWidth = 3;
                ctx.value.stroke(flashingArea.value.path);
            }

            isHighlighted = !isHighlighted;
        }, 500) as unknown as number;
    }
};

// 在组件卸载时清除定时器
onUnmounted(() => {
    if (flashInterval.value) {
        clearInterval(flashInterval.value);
    }
});
</script>

<style scoped>
.floor-map-container {
    position: relative;
    display: inline-block;
}

.tooltip {
    background-color: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 14px;
    pointer-events: none;
    z-index: 1000;
}

.flashing-area {
    position: absolute;
    top: 65px;
    right: 0;
}

.controls {
    margin-bottom: 20px;
    top: 20px;
    left: 20px;
    display: flex;
    gap: 10px;
    justify-content: center;
    width: 100%;
}

.controls button {
    padding: 12px 24px;
    font-size: 16px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    transition: all 0.3s ease;
    background-color: #ffffff;
    color: #333;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.controls button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.draw-btn.active {
    background-color: #4CAF50;
    color: white;
}

.erase-draw-btn {
    background-color: #ff4444 !important;
    color: white !important;
}

.show-all-btn {
    background-color: #2196F3 !important;
    color: white !important;
}

.area-dialog {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.dialog-content {
    background-color: white;
    padding: 20px;
    border-radius: 8px;
    width: 500px;
    max-height: 80vh;
    overflow-y: auto;
}

.form-group {
    margin-bottom: 15px;
    text-align: left;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

.form-group input[type="text"],
.form-group textarea {
    width: 97%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.form-group textarea {
    height: 100px;
    resize: vertical;
}

.teacher-input {
    display: flex;
    gap: 10px;
    margin-bottom: 10px;
}

.teacher-input input {
    flex: 1;
}

.remove-btn,
.confirm-btn,
.cancel-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.add-btn {
    background-color: #4CAF50;
    color: white;
    width: 100%;
    margin-top: 10px;
}

.remove-btn {
    background-color: #f44336;
    color: white;
}

.dialog-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 20px;
}

.confirm-btn {
    background-color: #2196F3;
    color: white;
}

.cancel-btn {
    background-color: #9e9e9e;
    color: white;
}

.search-box {
    flex: 1;
    width: 50px;
    max-width: 300px;
}

.search-box input {
    width: 80%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 16px;
    outline: none;
    transition: border-color 0.3s ease;
}

.search-box input:focus {
    border-color: #2196F3;
    box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.1);
}
</style>