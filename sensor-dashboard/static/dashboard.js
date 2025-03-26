// Initialize Socket.IO connection
const socket = io();

// Global variables
let lastUpdateTime = new Date();
let dataHistory = {
    timestamps: [],
    accelerometer: { x: [], y: [], z: [] }
};

// Maximum data points to keep in history
const MAX_HISTORY_LENGTH = 100;

// DOM elements
const elements = {
    accelerometer: {
        x: { value: document.getElementById('acc-x-value'), bar: document.getElementById('acc-x-bar') },
        y: { value: document.getElementById('acc-y-value'), bar: document.getElementById('acc-y-bar') },
        z: { value: document.getElementById('acc-z-value'), bar: document.getElementById('acc-z-bar') }
    },
    status: {
        indicator: document.getElementById('status-indicator'),
        text: document.getElementById('status-text')
    },
    table: document.getElementById('readings-table-body'),
    loadMoreBtn: document.getElementById('load-more-btn')
};

// Initialize Chart.js
const ctx = document.getElementById('accelerometer-chart').getContext('2d');
const accelerometerChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'X-Axis',
                data: [],
                borderColor: 'rgba(59, 130, 246, 0.8)',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                tension: 0.4
            },
            {
                label: 'Y-Axis',
                data: [],
                borderColor: 'rgba(16, 185, 129, 0.8)',
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                tension: 0.4
            },
            {
                label: 'Z-Axis',
                data: [],
                borderColor: 'rgba(239, 68, 68, 0.8)',
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                tension: 0.4
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
                    text: 'Acceleration (g)'
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

// Update the accelerometer bar graphs
function updateBarGraph(value, element, maxValue) {
    // Calculate percentage (mapping from -maxValue to +maxValue to 0-100%)
    const percentage = ((value + maxValue) / (2 * maxValue)) * 100;
    element.style.width = `${Math.min(Math.max(percentage, 0), 100)}%`;
}

// Format date for table display
function formatDate(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
}

// Add a new reading to the table
function addTableRow(data, prepend = true) {
    const row = document.createElement('tr');
    
    // Format the time
    const timeCell = document.createElement('td');
    timeCell.className = 'px-6 py-4 whitespace-nowrap text-sm text-gray-500';
    timeCell.textContent = formatDate(data.timestamp);
    row.appendChild(timeCell);
    
    // X value
    const xCell = document.createElement('td');
    xCell.className = 'px-6 py-4 whitespace-nowrap text-sm text-gray-500';
    xCell.textContent = data.accelerometer.x.toFixed(3);
    row.appendChild(xCell);
    
    // Y value
    const yCell = document.createElement('td');
    yCell.className = 'px-6 py-4 whitespace-nowrap text-sm text-gray-500';
    yCell.textContent = data.accelerometer.y.toFixed(3);
    row.appendChild(yCell);
    
    // Z value
    const zCell = document.createElement('td');
    zCell.className = 'px-6 py-4 whitespace-nowrap text-sm text-gray-500';
    zCell.textContent = data.accelerometer.z.toFixed(3);
    row.appendChild(zCell);
    
    // Add to the table
    if (prepend) {
        elements.table.insertBefore(row, elements.table.firstChild);
        
        // Limit number of rows displayed
        if (elements.table.children.length > 10) {
            elements.table.removeChild(elements.table.lastChild);
        }
    } else {
        elements.table.appendChild(row);
    }
}

// Load historical data from the server
function loadHistoricalData() {
    fetch('/api/history')
        .then(response => response.json())
        .then(data => {
            // Clear existing rows
            elements.table.innerHTML = '';
            
            // Add data to table
            data.forEach(record => {
                const timestamp = new Date(record.timestamp).getTime() / 1000;
                addTableRow({
                    timestamp: timestamp,
                    accelerometer: {
                        x: record.acc_x,
                        y: record.acc_y,
                        z: record.acc_z
                    }
                }, false);
            });
            
            // Update chart with historical data
            if (data.length > 0) {
                // Sort by timestamp ascending
                data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                
                // Extract data for chart
                const timestamps = data.map(record => new Date(record.timestamp));
                const xValues = data.map(record => record.acc_x);
                const yValues = data.map(record => record.acc_y);
                const zValues = data.map(record => record.acc_z);
                
                // Update chart data
                accelerometerChart.data.labels = timestamps;
                accelerometerChart.data.datasets[0].data = xValues;
                accelerometerChart.data.datasets[1].data = yValues;
                accelerometerChart.data.datasets[2].data = zValues;
                accelerometerChart.update();
                
                // Update data history for real-time updates
                dataHistory.timestamps = timestamps;
                dataHistory.accelerometer.x = xValues;
                dataHistory.accelerometer.y = yValues;
                dataHistory.accelerometer.z = zValues;
            }
        })
        .catch(error => {
            console.error('Error loading historical data:', error);
        });
}

// Update the UI with new sensor data
function updateUI(data) {
    // Update status
    lastUpdateTime = new Date();
    elements.status.indicator.className = 'inline-block h-4 w-4 rounded-full bg-green-500 mr-2';
    elements.status.text.textContent = 'Connected';
    
    // Update accelerometer values
    elements.accelerometer.x.value.textContent = data.accelerometer.x.toFixed(3);
    elements.accelerometer.y.value.textContent = data.accelerometer.y.toFixed(3);
    elements.accelerometer.z.value.textContent = data.accelerometer.z.toFixed(3);
    
    // Update bar graphs
    updateBarGraph(data.accelerometer.x, elements.accelerometer.x.bar, 2);
    updateBarGraph(data.accelerometer.y, elements.accelerometer.y.bar, 2);
    updateBarGraph(data.accelerometer.z, elements.accelerometer.z.bar, 2);
    
    // Add data to history
    const timestamp = new Date();
    dataHistory.timestamps.push(timestamp);
    dataHistory.accelerometer.x.push(data.accelerometer.x);
    dataHistory.accelerometer.y.push(data.accelerometer.y);
    dataHistory.accelerometer.z.push(data.accelerometer.z);
    
    // Limit history length
    if (dataHistory.timestamps.length > MAX_HISTORY_LENGTH) {
        dataHistory.timestamps.shift();
        dataHistory.accelerometer.x.shift();
        dataHistory.accelerometer.y.shift();
        dataHistory.accelerometer.z.shift();
    }
    
    // Update chart
    accelerometerChart.data.labels = dataHistory.timestamps;
    accelerometerChart.data.datasets[0].data = dataHistory.accelerometer.x;
    accelerometerChart.data.datasets[1].data = dataHistory.accelerometer.y;
    accelerometerChart.data.datasets[2].data = dataHistory.accelerometer.z;
    accelerometerChart.update();
    
    // Add to table
    addTableRow(data);
}

// Socket.IO event handlers
socket.on('connect', () => {
    elements.status.indicator.className = 'inline-block h-4 w-4 rounded-full bg-green-500 mr-2';
    elements.status.text.textContent = 'Connected';
    
    // Load historical data
    loadHistoricalData();
});

socket.on('disconnect', () => {
    elements.status.indicator.className = 'inline-block h-4 w-4 rounded-full bg-red-500 mr-2';
    elements.status.text.textContent = 'Disconnected';
});

socket.on('sensor_data', (data) => {
    updateUI(data);
});

// Load more button handler
elements.loadMoreBtn.addEventListener('click', () => {
    loadHistoricalData();
});

// Initial load of historical data
loadHistoricalData();

// Check connection status periodically
setInterval(() => {
    const now = new Date();
    const timeSinceLastUpdate = now - lastUpdateTime;
    
    // If we haven't received data for more than 5 seconds
    if (timeSinceLastUpdate > 5000 && elements.status.text.textContent === 'Connected') {
        elements.status.indicator.className = 'inline-block h-4 w-4 rounded-full bg-yellow-500 mr-2';
        elements.status.text.textContent = 'Connection issue';
        
        // Try to get the latest reading from the server
        fetch('/api/current')
            .then(response => response.json())
            .then(data => {
                if (!data.error) {
                    updateUI(data);
                    elements.status.indicator.className = 'inline-block h-4 w-4 rounded-full bg-green-500 mr-2';
                    elements.status.text.textContent = 'Connected';
                }
            })
            .catch(error => {
                console.error('Error fetching current data:', error);
            });
    }
    
    // If we haven't received data for more than 15 seconds
    if (timeSinceLastUpdate > 15000) {
        elements.status.indicator.className = 'inline-block h-4 w-4 rounded-full bg-red-500 mr-2';
        elements.status.text.textContent = 'Disconnected';
    }
}, 5000);