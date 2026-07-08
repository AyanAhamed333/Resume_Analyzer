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

    // --------------------------------------------------------------------------
    // RAG CHAT TAB IMPLEMENTATION
    // --------------------------------------------------------------------------

    const tabAnalyzerBtn = document.getElementById('tab-analyzer-btn');
    const tabChatBtn = document.getElementById('tab-chat-btn');
    const analyzerPanel = document.getElementById('analyzer-panel');
    const chatPanel = document.getElementById('chat-panel');

    // Tab Switching Handlers
    tabAnalyzerBtn.addEventListener('click', () => {
        tabAnalyzerBtn.classList.add('active');
        tabChatBtn.classList.remove('active');
        analyzerPanel.classList.remove('hidden');
        chatPanel.classList.add('hidden');
    });

    tabChatBtn.addEventListener('click', () => {
        tabChatBtn.classList.add('active');
        tabAnalyzerBtn.classList.remove('active');
        chatPanel.classList.remove('hidden');
        analyzerPanel.classList.add('hidden');
    });

    // Chat DOM Elements
    const chatPdfUpload = document.getElementById('chatPdfUpload');
    const chatUploadStatus = document.getElementById('chatUploadStatus');
    const chatStatusBadge = document.getElementById('chatStatusBadge');
    const chatMessages = document.getElementById('chatMessages');
    const quickPrompts = document.getElementById('quickPrompts');
    const chatInput = document.getElementById('chatInput');
    const chatSendBtn = document.getElementById('chatSendBtn');

    // Helper: Scroll chat to bottom
    const scrollToBottom = () => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };
    // Helper: Parse markdown content into structured HTML safely
    const parseMarkdown = (text) => {
        if (!text) return "";
        
        // Escape HTML to prevent XSS
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
            
        // Bold formatting: **text** -> <strong>text</strong>
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Line-by-line processing for lists
        const lines = html.split('\n');
        let inList = false;
        const processed = [];
        
        lines.forEach(line => {
            const trimmed = line.trim();
            // Match standard bullet symbols (*, -) or common unicode bullets (•, -, etc.)
            const bulletMatch = trimmed.match(/^([*\-•\uFFFD]|\u2022)\s+(.*)$/);
            
            if (bulletMatch) {
                if (!inList) {
                    processed.push('<ul class="chat-list" style="margin-left: 1.5rem; margin-top: 0.5rem; margin-bottom: 0.5rem; list-style-type: disc;">');
                    inList = true;
                }
                processed.push(`<li style="margin-bottom: 0.25rem;">${bulletMatch[2]}</li>`);
            } else {
                if (inList) {
                    processed.push('</ul>');
                    inList = false;
                }
                processed.push(line);
            }
        });
        
        if (inList) {
            processed.push('</ul>');
        }
        
        return processed.join('\n').replace(/\n/g, '<br>');
    };

    // Helper: Append a message bubble to the timeline with source citations support
    const appendBubble = (text, sender, sources = []) => {
        const bubble = document.createElement('div');
        bubble.classList.add('chat-bubble', `${sender}-bubble`);
        
        const content = document.createElement('div');
        content.classList.add('bubble-content');
        
        if (sender === 'assistant' || sender === 'user') {
            content.style.whiteSpace = 'normal';
            content.innerHTML = parseMarkdown(text);
        } else {
            content.textContent = text;
        }
        bubble.appendChild(content);
        
        // Source display removed per user request
        
        chatMessages.appendChild(bubble);
        scrollToBottom();
        return bubble;
    };

    // Handle Chat PDF upload
    chatPdfUpload.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        if (!file.name.toLowerCase().endsWith('.pdf')) {
            chatUploadStatus.textContent = "Please upload a valid PDF file.";
            chatUploadStatus.style.color = "var(--warning-color)";
            return;
        }

        chatUploadStatus.textContent = "Extracting text and indexing embeddings...";
        chatUploadStatus.style.color = "var(--text-muted)";
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload-resume', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                chatUploadStatus.textContent = `Resume indexed successfully! (${data.chunks} chunks in ${data.processing_time})`;
                chatUploadStatus.style.color = "var(--success-color)";
                
                // Update badge and enable inputs
                chatStatusBadge.textContent = "🟢 Resume Indexed";
                chatStatusBadge.className = "status-badge badge-green";
                chatInput.disabled = false;
                chatSendBtn.disabled = false;
                chatInput.placeholder = "Ask a question about the resume...";
                
                // Dynamically populate suggested questions
                if (data.suggested_questions && data.suggested_questions.length > 0) {
                    const container = quickPrompts.querySelector('.quick-prompts-container');
                    if (container) {
                        container.innerHTML = '';
                        data.suggested_questions.forEach(q => {
                            const btn = document.createElement('button');
                            btn.className = 'quick-prompt-btn';
                            btn.textContent = q;
                            btn.addEventListener('click', () => {
                                chatInput.value = q;
                                handleSendMessage();
                            });
                            container.appendChild(btn);
                        });
                    }
                }
                
                // Display quick prompts
                quickPrompts.classList.remove('hidden');

                // Append system notification bubble
                appendBubble("Resume uploaded and indexed. You can now chat! Ask me anything about this candidate.", "system");
            } else {
                chatUploadStatus.textContent = data.detail || "Failed to index resume.";
                chatUploadStatus.style.color = "var(--warning-color)";
            }
        } catch (error) {
            chatUploadStatus.textContent = "An error occurred during indexing.";
            chatUploadStatus.style.color = "var(--warning-color)";
            console.error(error);
        }
    });

    // Chat communication trigger function
    const handleSendMessage = async () => {
        const question = chatInput.value.trim();
        if (!question) return;

        // Add user bubble
        appendBubble(question, "user");
        chatInput.value = "";

        // Disable input during request
        chatInput.disabled = true;
        chatSendBtn.disabled = true;
        const loader = chatSendBtn.querySelector('.loader');
        const btnText = chatSendBtn.querySelector('.btn-text');
        loader.classList.remove('hidden');
        btnText.textContent = "";

        // Append temporary loading bubble for bot
        const loadingBubble = appendBubble("Thinking...", "assistant");
        loadingBubble.style.opacity = "0.7";

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question: question })
            });

            const data = await response.json();
            
            // Remove loading placeholder
            loadingBubble.remove();

            if (response.ok) {
                appendBubble(data.answer, "assistant", data.sources);
            } else {
                appendBubble(`Error: ${data.detail || "Failed to generate answer."}`, "system");
            }
        } catch (error) {
            loadingBubble.remove();
            appendBubble("An error occurred. Please verify your connection and Groq API settings.", "system");
            console.error(error);
        } finally {
            // Restore inputs
            chatInput.disabled = false;
            chatSendBtn.disabled = false;
            loader.classList.add('hidden');
            btnText.textContent = "Send";
            chatInput.focus();
            scrollToBottom();
        }
    };

    // Keyboard and click triggers
    chatSendBtn.addEventListener('click', handleSendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Handle Quick Prompts
    document.querySelectorAll('.quick-prompt-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            chatInput.value = e.target.textContent;
            handleSendMessage();
        });
    });
});
