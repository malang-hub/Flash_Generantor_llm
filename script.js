
let currentFlashcards = [];

// Tab switching functionality
function switchTab(tabName) {
    // Remove active class from all tabs and content
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Add active class to selected tab and content
    document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Clear form data when switching tabs
    if (tabName === 'text') {
        document.getElementById('file-input').value = '';
    } else {
        document.getElementById('content').value = '';
    }
}

// File input change handler
document.getElementById('file-input').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const label = document.querySelector('.file-upload label span');
        label.textContent = `📁 ${file.name}`;
    }
});

// Form submission handler
document.getElementById('flashcard-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const generateBtn = document.getElementById('generate-btn');
    const btnText = generateBtn.querySelector('.btn-text');
    const spinner = generateBtn.querySelector('.loading-spinner');
    const errorDiv = document.getElementById('error-message');
    
    // Show loading state
    generateBtn.disabled = true;
    btnText.style.display = 'none';
    spinner.style.display = 'inline';
    errorDiv.style.display = 'none';
    
    try {
        const formData = new FormData();
        
        // Get content from active tab
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab.id === 'text-tab') {
            const content = document.getElementById('content').value.trim();
            if (!content) {
                throw new Error('Please enter some text content');
            }
            formData.append('content', content);
        } else {
            const fileInput = document.getElementById('file-input');
            if (!fileInput.files[0]) {
                throw new Error('Please select a file');
            }
            formData.append('file', fileInput.files[0]);
        }
        
        const response = await fetch('/generate_flashcards', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate flashcards');
        }
        
        currentFlashcards = data;
        displayFlashcards(data);
        
    } catch (error) {
        console.error('Error:', error);
        errorDiv.textContent = error.message;
        errorDiv.style.display = 'block';
    } finally {
        // Reset button state
        generateBtn.disabled = false;
        btnText.style.display = 'inline';
        spinner.style.display = 'none';
    }
});

// Display flashcards
function displayFlashcards(flashcards) {
    const section = document.getElementById('flashcards-section');
    const statsDiv = document.getElementById('flashcards-stats');
    const outputDiv = document.getElementById('flashcards-output');
    
    // Show stats
    statsDiv.innerHTML = `
        <h3>📊 Generation Summary</h3>
        <p><strong>${flashcards.length}</strong> flashcards generated successfully!</p>
    `;
    
    // Clear previous output
    outputDiv.innerHTML = '';
    
    // Create flashcard elements
    flashcards.forEach((card, index) => {
        const cardDiv = document.createElement('div');
        cardDiv.classList.add('flashcard');
        
        const difficultyClass = `difficulty-${card.difficulty.toLowerCase()}`;
        
        cardDiv.innerHTML = `
            <div class="topic-tag">${card.topic || 'General'}</div>
            <div class="flashcard-header">
                <span class="flashcard-number">Card ${index + 1}</span>
                <span class="difficulty-badge ${difficultyClass}">${card.difficulty}</span>
            </div>
            <h3>❓ ${card.question}</h3>
            <div class="flashcard-answer">
                <strong>💡 Answer:</strong> ${card.answer}
            </div>
        `;
        
        outputDiv.appendChild(cardDiv);
    });
    
    // Show the section
    section.style.display = 'block';
    
    // Scroll to results
    section.scrollIntoView({ behavior: 'smooth' });
}

// Export functionality
function exportFlashcards(format) {
    if (!currentFlashcards.length) {
        alert('No flashcards to export!');
        return;
    }
    
    const dataParam = encodeURIComponent(JSON.stringify(currentFlashcards));
    const url = `/export/${format}?data=${dataParam}`;
    
    // Create temporary link and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = `flashcards.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Set default tab
    switchTab('text');
});

