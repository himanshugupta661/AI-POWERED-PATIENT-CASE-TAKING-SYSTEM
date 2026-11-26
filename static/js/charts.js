/**
 * Chart.js Integration for Doctor Dashboard
 * Renders status breakdown doughnut chart and intake trends
 */

function initDoctorCharts(statusData) {
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js library not loaded.');
        return;
    }

    // 1. Status Distribution Doughnut Chart
    const statusCanvas = document.getElementById('statusChart');
    if (statusCanvas && statusData) {
        const labels = Object.keys(statusData);
        const dataValues = Object.values(statusData);

        new Chart(statusCanvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: dataValues,
                    backgroundColor: [
                        '#f59e0b', // Submitted (warning orange)
                        '#0284c7', // In Review (medical blue)
                        '#2563eb', // Reviewed (primary blue)
                        '#10b981'  // Completed (emerald green)
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            font: { size: 12, family: 'sans-serif', weight: '600' }
                        }
                    }
                },
                cutout: '68%'
            }
        });
    }

    // 2. Weekly Intake Trend Bar Chart
    const trendCanvas = document.getElementById('trendChart');
    if (trendCanvas) {
        new Chart(trendCanvas, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Intake Cases',
                    data: [3, 5, 4, 7, 6, 8, 4],
                    backgroundColor: '#0284c7',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 2 }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}
