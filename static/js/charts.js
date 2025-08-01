/**
 * Charts and visualization JavaScript for the Scout Management Application
 * Uses Chart.js for visualizations
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard charts
    initDashboardCharts();
});

/**
 * Initialize dashboard charts
 */
function initDashboardCharts() {
    // Get the table stats chart canvas
    const tableStatsCanvas = document.getElementById('tableStatsChart');
    if (!tableStatsCanvas) return;
    
    // Parse the data from the data attribute or custom script variables
    const tableStatsElement = document.getElementById('tableStatsData');
    let tableStats = [];
    
    if (tableStatsElement) {
        try {
            tableStats = JSON.parse(tableStatsElement.textContent);
        } catch (e) {
            console.error('Error parsing table stats data:', e);
        }
    } else {
        // Try to read from window variables
        if (window.tableStatsData) {
            tableStats = window.tableStatsData;
        }
    }
    
    if (tableStats.length === 0) return;
    
    // Create configuration for the pie chart
    const labels = tableStats.map(item => item.name);
    const data = tableStats.map(item => item.count);
    
    // Use color scheme
    const backgroundColors = [
        'rgba(54, 162, 235, 0.7)',   // Blue
        'rgba(255, 99, 132, 0.7)',   // Red
        'rgba(75, 192, 192, 0.7)',   // Green
        'rgba(255, 206, 86, 0.7)',   // Yellow
        'rgba(153, 102, 255, 0.7)',  // Purple
        'rgba(255, 159, 64, 0.7)',   // Orange
        'rgba(199, 199, 199, 0.7)',  // Gray
        'rgba(83, 102, 255, 0.7)',   // Indigo
        'rgba(78, 235, 133, 0.7)',   // Mint
        'rgba(255, 99, 71, 0.7)'     // Tomato
    ];
    
    // Create the chart
    new Chart(tableStatsCanvas, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors.slice(0, labels.length),
                borderWidth: 1,
                borderColor: backgroundColors.map(color => color.replace('0.7', '1'))
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#ffffff',
                        padding: 10,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            animation: {
                animateScale: true,
                animateRotate: true
            }
        }
    });
}

/**
 * Create a bar chart for table data
 * @param {string} canvasId - ID of the canvas element
 * @param {Array} data - Data for the chart
 * @param {Object} options - Custom options
 */
function createBarChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data) return;
    
    const ctx = canvas.getContext('2d');
    
    const defaultOptions = {
        indexBy: 'name',
        valueKey: 'value',
        labelKey: 'name',
        title: 'Données',
        color: 'rgba(54, 162, 235, 0.7)'
    };
    
    const chartOptions = { ...defaultOptions, ...options };
    
    const labels = data.map(item => item[chartOptions.labelKey]);
    const values = data.map(item => item[chartOptions.valueKey]);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: chartOptions.title,
                data: values,
                backgroundColor: chartOptions.color,
                borderColor: chartOptions.color.replace('0.7', '1'),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: chartOptions.title,
                    color: '#ffffff',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

/**
 * Create a line chart for time series data
 * @param {string} canvasId - ID of the canvas element
 * @param {Array} data - Data for the chart
 * @param {Object} options - Custom options
 */
function createLineChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data) return;
    
    const ctx = canvas.getContext('2d');
    
    const defaultOptions = {
        xKey: 'date',
        yKey: 'value',
        title: 'Tendance',
        color: 'rgba(75, 192, 192, 0.7)'
    };
    
    const chartOptions = { ...defaultOptions, ...options };
    
    // Sort data by date if xKey is 'date'
    if (chartOptions.xKey === 'date') {
        data.sort((a, b) => new Date(a[chartOptions.xKey]) - new Date(b[chartOptions.xKey]));
    }
    
    const labels = data.map(item => {
        if (chartOptions.xKey === 'date') {
            return formatDate(item[chartOptions.xKey]);
        }
        return item[chartOptions.xKey];
    });
    
    const values = data.map(item => item[chartOptions.yKey]);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: chartOptions.title,
                data: values,
                backgroundColor: chartOptions.color,
                borderColor: chartOptions.color.replace('0.7', '1'),
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: chartOptions.title,
                    color: '#ffffff',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

/**
 * Format date for display in charts
 * @param {string} dateStr - Date string
 * @returns {string} - Formatted date
 */
function formatChartDate(dateStr) {
    if (!dateStr) return '';
    
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return dateStr;
        
        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: '2-digit'
        });
    } catch (e) {
        console.error('Error formatting date', e);
        return dateStr;
    }
}

/**
 * Generate analytical dashboard for a specific table
 * @param {string} containerId - ID of the container element
 * @param {Array} records - Array of record objects
 * @param {Array} fields - Array of field objects
 */
function generateTableAnalytics(containerId, records, fields) {
    const container = document.getElementById(containerId);
    if (!container || !records || !fields) return;
    
    // Clear the container
    container.innerHTML = '';
    
    // Create row for charts
    const row = document.createElement('div');
    row.className = 'row g-4 mb-4';
    
    // Create stats card
    const statsCard = document.createElement('div');
    statsCard.className = 'col-md-4';
    statsCard.innerHTML = `
        <div class="card h-100">
            <div class="card-header bg-dark">
                <h5 class="mb-0"><i class="fas fa-chart-pie me-2"></i>Statistiques</h5>
            </div>
            <div class="card-body">
                <div class="d-flex flex-column gap-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>Nombre d'enregistrements</div>
                        <div class="badge bg-primary">${records.length}</div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <div>Date du dernier enregistrement</div>
                        <div class="badge bg-info">
                            ${records.length > 0 ? formatChartDate(records[0].created_at) : 'N/A'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    row.appendChild(statsCard);
    
    // Find numeric fields for charts
    const numericFields = fields.filter(field => field.field_type === 'number');
    
    if (numericFields.length > 0) {
        // Create numeric chart card
        const chartCard = document.createElement('div');
        chartCard.className = 'col-md-8';
        chartCard.innerHTML = `
            <div class="card h-100">
                <div class="card-header bg-dark">
                    <h5 class="mb-0"><i class="fas fa-chart-bar me-2"></i>Distribution des valeurs</h5>
                </div>
                <div class="card-body">
                    <canvas id="numericDataChart" height="200"></canvas>
                </div>
            </div>
        `;
        row.appendChild(chartCard);
        
        // Get data for the first numeric field
        const firstNumericField = numericFields[0];
        const numericData = records.map(record => {
            const fieldValue = record.values[firstNumericField.name];
            return {
                name: formatChartDate(record.created_at),
                value: fieldValue || 0
            };
        }).filter(item => item.value !== null);
        
        // Add the row to the container
        container.appendChild(row);
        
        // Initialize the chart after adding to the DOM
        setTimeout(() => {
            createBarChart('numericDataChart', numericData, {
                title: firstNumericField.display_name,
                color: 'rgba(75, 192, 192, 0.7)'
            });
        }, 0);
    } else {
        // Just add the stats card if no numeric fields
        container.appendChild(row);
    }
    
    // Add dropdown field analysis if applicable
    const dropdownFields = fields.filter(field => field.field_type === 'dropdown');
    
    if (dropdownFields.length > 0) {
        dropdownFields.forEach(field => {
            // Create card for dropdown distribution
            const dropdownRow = document.createElement('div');
            dropdownRow.className = 'row mb-4';
            
            const dropdownCard = document.createElement('div');
            dropdownCard.className = 'col-12';
            dropdownCard.innerHTML = `
                <div class="card">
                    <div class="card-header bg-dark">
                        <h5 class="mb-0"><i class="fas fa-chart-pie me-2"></i>Distribution de ${field.display_name}</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="dropdown_${field.id}_chart" height="200"></canvas>
                    </div>
                </div>
            `;
            dropdownRow.appendChild(dropdownCard);
            container.appendChild(dropdownRow);
            
            // Calculate distribution data
            const options = field.options || [];
            const distribution = {};
            
            options.forEach(option => {
                distribution[option] = 0;
            });
            
            records.forEach(record => {
                const value = record.values[field.name];
                if (value && distribution[value] !== undefined) {
                    distribution[value]++;
                }
            });
            
            // Format data for chart
            const chartData = Object.keys(distribution).map(key => ({
                name: key,
                value: distribution[key]
            }));
            
            // Initialize the chart
            setTimeout(() => {
                createBarChart(`dropdown_${field.id}_chart`, chartData, {
                    title: `Distribution de ${field.display_name}`,
                    color: 'rgba(54, 162, 235, 0.7)'
                });
            }, 0);
        });
    }
}
