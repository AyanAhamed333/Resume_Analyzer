document.addEventListener('DOMContentLoaded', () => {
    const pdfUpload = document.getElementById('pdfUpload');
    const uploadStatus = document.getElementById('uploadStatus');
    const resumeText = document.getElementById('resumeText');
    const roleSelect = document.getElementById('roleSelect');
    const jdText = document.getElementById('jdText');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analyzeStatus = document.getElementById('analyzeStatus');
    const btnText = analyzeBtn.querySelector('.btn-text');
    const loader = analyzeBtn.querySelector('.loader');
    
    // Results elements
    const resultsSection = document.getElementById('resultsSection');
    const scoreValueText = document.getElementById('scoreValueText');
    const scoreProgressBar = document.getElementById('scoreProgressBar');
    const skillsFoundList = document.getElementById('skillsFoundList');
    const missingSkillsList = document.getElementById('missingSkillsList');
    const suggestionsList = document.getElementById('suggestionsList');

    // Handle PDF Upload
    pdfUpload.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        if (!file.name.toLowerCase().endsWith('.pdf')) {
            uploadStatus.textContent = "Please upload a valid PDF file.";
            uploadStatus.style.color = "var(--warning-color)";
            return;
        }

        uploadStatus.textContent = "Extracting text from PDF...";
        uploadStatus.style.color = "var(--text-muted)";
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                resumeText.value = data.text;
                uploadStatus.textContent = "Text extracted successfully!";
                uploadStatus.style.color = "var(--success-color)";
            } else {
                uploadStatus.textContent = data.error || "Failed to extract text.";
                uploadStatus.style.color = "var(--warning-color)";
            }
        } catch (error) {
            uploadStatus.textContent = "An error occurred during upload.";
            uploadStatus.style.color = "var(--warning-color)";
            console.error(error);
        }
    });

    // Handle Analyze Button
    analyzeBtn.addEventListener('click', async () => {
        const text = resumeText.value.trim();
        const role = roleSelect.value;
        const jd = jdText.value.trim();

        // Validation
        if (!text) {
            analyzeStatus.textContent = "Please paste resume text or upload a PDF.";
            return;
        }
        if (!role && !jd) {
            analyzeStatus.textContent = "Please select a target role or paste a Job Description.";
            return;
        }

        analyzeStatus.textContent = "";
        
        // UI Loading State
        analyzeBtn.disabled = true;
        btnText.textContent = "Analyzing...";
        loader.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        
        // Reset Progress bar
        scoreProgressBar.style.width = '0%';

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    resume_text: text,
                    role: role,
                    jd_text: jd
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                displayResults(data);
            } else {
                analyzeStatus.textContent = data.error || "Analysis failed.";
            }
        } catch (error) {
            analyzeStatus.textContent = "An error occurred during analysis.";
            console.error(error);
        } finally {
            // Restore UI State
            analyzeBtn.disabled = false;
            btnText.textContent = "Analyze Resume";
            loader.classList.add('hidden');
        }
    });

    function displayResults(data) {
        // Show results section
        resultsSection.classList.remove('hidden');
        
        // Populate Score
        scoreValueText.textContent = `${data.score}%`;
        
        // Update color based on score
        if (data.score >= 70) {
            scoreValueText.style.color = "#10b981"; // success
            scoreProgressBar.style.background = "linear-gradient(to right, #10b981, #34d399)";
        } else if (data.score >= 40) {
            scoreValueText.style.color = "#f59e0b"; // warning (amber)
            scoreProgressBar.style.background = "linear-gradient(to right, #f59e0b, #fbbf24)";
        } else {
            scoreValueText.style.color = "#f43f5e"; // error (rose)
            scoreProgressBar.style.background = "linear-gradient(to right, #f43f5e, #fb7185)";
        }

        // Animate progress bar slightly delayed for visual effect
        setTimeout(() => {
            scoreProgressBar.style.width = `${data.score}%`;
        }, 100);

        // Populate Skills Found
        skillsFoundList.innerHTML = '';
        if (data.skills_found.length === 0) {
            skillsFoundList.innerHTML = '<li>None found</li>';
        } else {
            data.skills_found.forEach(skill => {
                const li = document.createElement('li');
                li.textContent = skill;
                skillsFoundList.appendChild(li);
            });
        }

        // Populate Missing Skills
        missingSkillsList.innerHTML = '';
        if (data.missing_skills.length === 0) {
            missingSkillsList.innerHTML = '<li>None!</li>';
        } else {
            data.missing_skills.forEach(skill => {
                const li = document.createElement('li');
                li.textContent = skill;
                missingSkillsList.appendChild(li);
            });
        }

        // Populate Suggestions
        suggestionsList.innerHTML = '';
        if (data.suggestions.length === 0) {
            suggestionsList.innerHTML = '<li>Your resume looks great!</li>';
        } else {
            data.suggestions.forEach(suggestion => {
                const li = document.createElement('li');
                li.textContent = suggestion;
                suggestionsList.appendChild(li);
            });
        }
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
});
