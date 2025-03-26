// Initialize Socket.IO connection
const socket = io();

// Global variables
let lastUpdateTime = new Date();
let dataHistory = {
    timestamps: [],
    accelerometer: { x: [], y: [], z: [] },
    gyroscope: { x: [], y: [], z: [] },
    orientation: { roll: [], pitch: [] },
    temperature: []
};

// Maximum data points to keep in history
const MAX_HISTORY_LENGTH = 100;

// DOM elements
const elements = {
    temperature: document.getElementById('temperature-value'),
    roll: document.getElementById('roll-value'),
    pitch: document.getElementById('pitch-value'),
    status: {
        indicator: document.getElementById('status-indicator'),
        text: document.getElementById('status-text'),
        lastUpdate: document.getElementById('last-update')
    },
    accelerometer: {
        x: { value: document.getElementById('acc-x-value'), bar: document.getElementById('acc-x-bar') },
        y: { value: document.getElementById('acc-y-value'), bar: document.getElementById('acc-y-bar') },
        z: { value: document.getElementById('acc-z-value'), bar: document.getElementById('acc-z-bar') }
    },
    gyroscope: {
        x: { value: document.getElementById('gyro-x-value'), bar: document.getElementById('gyro-x-bar') },
        y: { value: document.getElementById('gyro-y-value'), bar: document.getElementById('gyro-y-bar') },
        z: { value: document.getElementById('gyro-z-value'), bar: document.getElementById('gyro-z-bar') }
    }
};

// Initialize 3D visualization
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
const orientationCanvas = document.getElementById('orientation-canvas');

function initOrientationVisualization() {
    // Set renderer
    renderer.setSize(orientationCanvas.clientWidth, orientationCanvas.clientHeight);
    renderer.setClearColor(0xf3f4f6, 1);
    orientationCanvas.appendChild(renderer.domElement);

    // Create a box geometry for the IMU
    const geometry = new THREE.BoxGeometry(1, 0.2, 1.5);
    
    // Materials for different faces with slight transparency
    const materials = [
        new THREE.MeshBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.7 }), // right
        new THREE.MeshBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.7 }), // left
        new THREE.MeshBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.7 }), // top
        new THREE.MeshBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.7 }), // bottom
        new THREE.MeshBasicMaterial({ color: 0xef4444, transparent: true, opacity: 0.7 }), // front
        new THREE.MeshBasicMaterial({ color: 0xef4444, transparent: true, opacity: 0.7 })  // back
    ];
    
    // Create a mesh with geometry and material
    const cube = new THREE.Mesh(geometry, materials);
    scene.add(cube);
    
    // Add coordinate axes
    const axesHelper = new THREE.AxesHelper(2);
    scene.add(axesHelper);
    
    // Position camera
    camera.position.z = 3;
    camera.position.y = 1;
    camera.lookAt(0, 0, 0);
    
    return cube;
}

const imuCube = initOrientationVisualization();

// Initialize Chart.js
const ctx = document.getElementById('motion-chart').getContext('2d');
const motionChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Accel X',
                data: [],
                borderColor: 'rgba(59, 130, 246, 0.8)',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                tension: 0.4,
                hidden: true
            },
            {
                label: 'Accel Y',
                data: [],
                borderColor: 'rgba(16, 185, 129, 0.8)',
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                tension: 0.4,
                hidden: true
            },
            {
                label: 'Accel Z',
                data: [],
                borderColor: 'rgba(239, 68, 68, 0.8)',
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                tension: 0.4,
                hidden: true
            },
            {
                label: 'Gyro X',
                data: [],
                borderColor: 'rgba(59, 130, 246, 0.8)',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderDash: [5, 5],
                tension: 0.4,
                hidden: true
            },
            {
                label: 'Gyro Y', 
                data: [],
                borderColor: 'rgba(16, 185, 129, 0.8)',
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                borderDash: [5, 5],
                tension: 0.4,
                hidden: true
            },
            {
                label: 'Gyro Z',
                data: [],
                borderColor: 'rgba(239, 68, 68, 0.8)',
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                borderDash: [5, 5],
                tension: 0.4,
                hidden: true
            },
            {
                label: 'Roll',
                data: [],
                borderColor: 'rgba(124, 58, 237, 0.8)',
                backgroundColor: 'rgba(124, 58, 237, 0.2)',
                tension: 0.4
            },
            {
                label: 'Pitch',
                data: [],
                borderColor: 'rgba(245, 158, 11, 0.8)',
                backgroundColor: 'rgba(245, 158, 11, 0.2)',
                tension: 0.4
            },
            {
                label: 'Temperature',
                data: [],
                borderColor: 'rgba(239, 68, 68, 0.8)',
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                tension: 0.4,
                hidden: true,
                yAxisID: 'y1'
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'second',
                    displayFormats: {
                        second: 'HH:mm:ss'
                    }
                },
                title: {
                    display: true,
                    text: 'Time'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Value'
                }
            },
            y1: {
                position: 'right',
                title: {
                    display: true,
                    text: 'Temperature (°C)'
                },
                grid: {
                    drawOnChartArea: false
                }
            }
        },
        plugins: {
            legend: {
                position: 'top'
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        }
    }
});

// Update the accelerometer and gyroscope bar graphs
function updateBarGraph(value, element, maxValue) {
    // Calculate percentage (mapping from -maxValue to +maxValue to 0-100%)
    const percentage = ((value + maxValue) / (2 * maxValue)) * 100;
    element.style.width = `${Math.min(Math.max(percentage, 0), 100)}%`;
}

// Update the 3D visualization
function updateOrientation(roll, pitch) {
    // Convert degrees to radians
    const rollRad = roll * (Math.PI / 180);
    const pitchRad = pitch * (Math.PI / 180);
    
    // Reset rotation
    imuCube.rotation.set(0, 0, 0);
    
    // Apply rotations in correct order
    imuCube.rotateX(pitchRad);
    imuCube.rotateZ(rollRad);
    
    // Render the scene
    renderer.render(scene, camera);
}

// Animate function for continuous rendering
function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
animate();

// Format time difference as string
function getTimeDiffString(date) {
    const diff = new Date() - date;
    if (diff < 1000) return 'Just now';
    if (diff < 60000) return `${Math.floor(diff / 1000)} seconds ago`;
    if (diff < 3600000) return `${Math.floor(diff / 60000)} minutes ago`;
    return `${Math.floor(diff / 3600000)} hours ago`;
}

// Update the UI with new sensor data
function updateUI(data) {
    // Update status
    lastUpdateTime = new Date();
    elements.status.indicator.className = 'inline-block h-4 w-4 rounded-full bg-green-500 mr-2';
    elements.status.text.textContent = 'Connected';
    elements.status.lastUpdate.textContent = 'Just now';
    
    // Update temperature
    elements.temperature.textContent = data.temperature.toFixed(1);
    
    // Update orientation
    elements.roll.textContent = `${data.orientation.roll.toFixed(1)}°`;
    elements.pitch.textContent = `${data.orientation.pitch.toFixed(1)}°`;
    
    // Update accelerometer values
    elements.accelerometer.x.value.textContent = data.accelerometer.x.toFixed(3);
    elements.accelerometer.y.value.textContent = data.accelerometer.y.toFixed(3);
    elements.accelerometer.z.value.textContent = data.accelerometer.z.toFixed(3);
    
    // Update gyroscope values
    elements.gyroscope.x.value.textContent = data.gyroscope.x.toFixed(3);
    elements.gyroscope.y.value.textContent = data.gyroscope.y.toFixed(3);
    elements.gyroscope.z.value.textContent = data.gyroscope.z.toFixed(3);
    
    // Update bar graphs
    updateBarGraph(data.accelerometer.x, elements.accelerometer.x.bar, 2);
    updateBarGraph(data.accelerometer.y, elements.accelerometer.y.bar, 2);
    updateBarGraph(data.accelerometer.z, elements.accelerometer.z.bar, 2);
    updateBarGraph(data.gyroscope.x, elements.gyroscope.x.bar, 250);
    updateBarGraph(data.gyroscope.y, elements.gyroscope.y.bar, 250);
    updateBarGraph(data.gyroscope.z, elements.gyroscope.z.bar, 250);
    
    // Update 3D visualization
    updateOrientation(data.orientation.roll, data.orientation.pitch);
    
    // Add data to history
    const timestamp = new Date();
    dataHistory.timestamps.push(timestamp);
    dataHistory.accelerometer.x.push(data.accelerometer.x);
    dataHistory.accelerometer.y.push(data.accelerometer.y);
    dataHistory.accelerometer.z.push(data.accelerometer.z);
    dataHistory.gyroscope.x.push(data.gyroscope.x);
    dataHistory.gyroscope.y.push(data.gyroscope.y);
    dataHistory.gyroscope.z.push(data.gyroscope.z);
    dataHistory.orientation.roll.push(data.orientation.roll);
    dataHistory.orientation.pitch.push(data.orientation.pitch);
    dataHistory.temperature.push(data.temperature);
    
    // Limit history length
    if (dataHistory.timestamps.length > MAX_HISTORY_LENGTH) {
        dataHistory.timestamps.shift();
        dataHistory.accelerometer.x.shift();
        dataHistory.accelerometer.y.shift();
        dataHistory.accelerometer.z.shift();
        dataHistory.gyroscope.x.shift();
        dataHistory.gyroscope.y.shift();
        dataHistory.gyroscope.z.shift();
        dataHistory.orientation.roll.shift();
        dataHistory.orientation.pitch.shift();
        dataHistory.temperature.shift();
    }
    
    // Update chart
    motionChart.data.labels = dataHistory.timestamps;
    motionChart.data.datasets[0].data = dataHistory.accelerometer.x;
    motionChart.data.datasets[1].data = dataHistory.accelerometer.y;
    motionChart.data.datasets[2].data = dataHistory.accelerometer.z;
    motionChart.data.datasets[3].data = dataHistory.gyroscope.x;
    motionChart.data.datasets[4].data = dataHistory.gyroscope.y;
    motionChart.data.datasets[5].data = dataHistory.gyroscope.z;
    motionChart.data.datasets[6].data = dataHistory.orientation.roll;
    motionChart.data.datasets[7].data = dataHistory.orientation.pitch;
    motionChart.data.datasets[8].data = dataHistory.temperature;
    motionChart.update();
}

// Socket.IO event handlers
socket.on('connect', () => {
    elements.status.indicator.className = 'inline-block h-4 w-4 rounded-full bg-green-500 mr-2';
    elements.status.text.textContent = 'Connected';
});

socket.on('disconnect', () => {
    elements.status.indicator.className = 'inline-block h-4 w-4 rounded-full bg-red-500 mr-2';
    elements.status.text.textContent = 'Disconnected';
});

socket.on('sensor_data', (data) => {
    updateUI(data);
});

// Update the "last update" text every second
setInterval(() => {
    if (elements.status.text.textContent === 'Connected') {
        elements.status.lastUpdate.textContent = getTimeDiffString(lastUpdateTime);
    }
    
    // If we haven't received data for more than 5 seconds, show warning
    if (new Date() - lastUpdateTime > 5000 && elements.status.text.textContent === 'Connected') {
        elements.status.indicator.className = 'inline-block h-4 w-4 rounded-full bg-yellow-500 mr-2';
        elements.status.text.textContent = 'Connection issue';
    }
    
    // If we haven't received data for more than 15 seconds, show disconnected
    if (new Date() - lastUpdateTime > 15000) {
        elements.status.indicator.className = 'inline-block h-4 w-4 rounded-full bg-red-500 mr-2';
        elements.status.text.textContent = 'Disconnected';
    }
}, 1000);

// Handle window resize
window.addEventListener('resize', () => {
    if (orientationCanvas.clientWidth > 0 && orientationCanvas.clientHeight > 0) {
        renderer.setSize(orientationCanvas.clientWidth, orientationCanvas.clientHeight);
        camera.aspect = orientationCanvas.clientWidth / orientationCanvas.clientHeight;
        camera.updateProjectionMatrix();
    }
});