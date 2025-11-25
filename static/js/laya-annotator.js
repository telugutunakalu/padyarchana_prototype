/**
 * Laya Audio Annotator for Padyarchana
 * Adapted from the original Laya transcript alignment tool
 */

const LayaAnnotator = {
    poemId: null,
    poemText: '',
    words: [],
    timestamps: {},
    flags: {},
    activeIndex: -1,
    audioUrl: '',
    unsavedChanges: false,

    init(poemId, poemText, audioUrl, existingAnnotations = []) {
        this.poemId = poemId;
        this.poemText = poemText;
        this.audioUrl = audioUrl;
        this.words = this.splitTextIntoWords(poemText);
        this.timestamps = {};
        this.flags = {};

        // Initialize timestamps with null values
        this.words.forEach((word, index) => {
            this.timestamps[index] = null;
        });

        // Load existing annotations if provided
        if (existingAnnotations && existingAnnotations.length > 0) {
            existingAnnotations.forEach(ann => {
                if (ann.word_index < this.words.length) {
                    this.timestamps[ann.word_index] = ann.timestamp_ms;
                    if (ann.flags) {
                        this.flags[ann.word_index] = ann.flags;
                    }
                }
            });
        }

        this.cacheElements();
        this.bindEvents();
        this.loadAudio();
        this.renderTranscript();
    },

    splitTextIntoWords(text) {
        // Split text into words, preserving Telugu characters
        // Split on whitespace and newlines, filter empty strings
        return text.split(/[\s\n]+/).filter(word => word.trim().length > 0);
    },

    cacheElements() {
        this.transcriptList = document.getElementById('transcriptList');
        this.audioSource = document.getElementById('audioSource');
        this.audioPlayer = document.getElementById('audioPlayer');
        this.saveBtn = document.getElementById('saveBtn');
        this.exportBtn = document.getElementById('exportBtn');
        this.statusMessage = document.getElementById('statusMessage');
    },

    bindEvents() {
        if (this.saveBtn) {
            this.saveBtn.addEventListener('click', () => this.saveAnnotations());
        }
        if (this.exportBtn) {
            this.exportBtn.addEventListener('click', () => this.exportCSV());
        }
        document.addEventListener('keydown', this.handleKeydown.bind(this));
        if (this.audioPlayer) {
            this.audioPlayer.addEventListener('timeupdate', this.handleTimeUpdate.bind(this));
        }

        // Warn before leaving if unsaved changes
        window.addEventListener('beforeunload', (e) => {
            if (this.unsavedChanges) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    },

    loadAudio() {
        if (this.audioSource && this.audioUrl) {
            this.audioSource.src = this.audioUrl;
            this.audioPlayer.load();
        }
    },

    renderTranscript() {
        if (!this.transcriptList) return;

        this.transcriptList.innerHTML = '';

        let i = 0;
        const total = this.words.length;
        const batchSize = 100;

        const renderBatch = () => {
            const end = Math.min(i + batchSize, total);
            for (; i < end; i++) {
                const listItem = this.createTranscriptLine(this.words[i], i);
                this.transcriptList.appendChild(listItem);
            }
            if (i < total) {
                requestAnimationFrame(renderBatch);
            }
        };

        requestAnimationFrame(renderBatch);
    },

    createTranscriptLine(word, index) {
        // Create table row instead of list item
        const row = document.createElement('tr');
        row.dataset.index = index;

        // Cell 1: Reset button
        const resetCell = document.createElement('td');
        const resetBtn = document.createElement('a');
        resetBtn.className = 'action-btn resetBtn';
        resetBtn.innerHTML = '<i class="bi bi-x-lg"></i>';
        resetBtn.title = 'Reset timestamp';
        resetBtn.addEventListener('click', () => this.resetStartTime(index));
        resetCell.appendChild(resetBtn);

        // Cell 2: Timestamp display
        const timestampCell = document.createElement('td');
        const timestampInput = document.createElement('input');
        timestampInput.type = 'text';
        const hasTime = this.timestamps[index] !== null;
        timestampInput.className = `timestamp form-control form-control-sm${hasTime ? ' has-time' : ''}`;
        timestampInput.style.width = '85px';
        timestampInput.readOnly = true;
        timestampInput.value = hasTime ? this.formatTime(this.timestamps[index]) : '--:--:--';
        timestampCell.appendChild(timestampInput);

        // Cell 3: Adjust buttons (- and +)
        const adjustCell = document.createElement('td');
        const adjustGroup = document.createElement('div');
        adjustGroup.className = 'adjust-btns';

        const minusBtn = document.createElement('a');
        minusBtn.className = 'action-btn minusBtn';
        minusBtn.innerHTML = '<i class="bi bi-dash-lg"></i>';
        minusBtn.title = '-50ms';
        minusBtn.addEventListener('click', () => this.adjustTimestamp(index, -50));

        const plusBtn = document.createElement('a');
        plusBtn.className = 'action-btn plusBtn';
        plusBtn.innerHTML = '<i class="bi bi-plus-lg"></i>';
        plusBtn.title = '+50ms';
        plusBtn.addEventListener('click', () => this.adjustTimestamp(index, 50));

        adjustGroup.append(minusBtn, plusBtn);
        adjustCell.appendChild(adjustGroup);

        // Cell 4: Play button
        const playCell = document.createElement('td');
        const playBtn = document.createElement('a');
        playBtn.className = 'action-btn playBtn';
        playBtn.innerHTML = '<i class="bi bi-play-fill"></i>';
        playBtn.title = 'Play from this timestamp';
        playBtn.addEventListener('click', () => this.playFromTimestamp(index));
        playCell.appendChild(playBtn);

        // Cell 5: Word display (read-only for Telugu text)
        const wordCell = document.createElement('td');
        wordCell.className = 'td-word';
        const wordSpan = document.createElement('span');
        wordSpan.className = 'telugu-text word-text';
        wordSpan.style.fontSize = '1.1rem';
        wordSpan.textContent = word;
        wordSpan.addEventListener('click', () => {
            this.updateActiveLine(index);
            if (this.timestamps[index] !== null) {
                this.audioPlayer.currentTime = this.timestamps[index] / 1000;
            }
        });
        wordCell.appendChild(wordSpan);

        // Cell 6: Flag button
        const flagCell = document.createElement('td');
        const flagBtn = document.createElement('a');
        flagBtn.className = `action-btn flagBtn${this.flags[index] ? ' flag-active' : ''}`;
        flagBtn.innerHTML = `<i class="bi ${this.flags[index] ? 'bi-flag-fill' : 'bi-flag'}"></i>`;
        flagBtn.title = 'Flag this word';
        flagBtn.addEventListener('click', () => this.openFlagModal(index, flagBtn));
        flagCell.appendChild(flagBtn);

        // Append all cells to row
        row.append(resetCell, timestampCell, adjustCell, playCell, wordCell, flagCell);

        return row;
    },

    formatTime(ms) {
        if (ms === null || ms === undefined) return '--:--:--';
        const minutes = Math.floor(ms / 60000).toString().padStart(2, '0');
        const seconds = Math.floor((ms % 60000) / 1000).toString().padStart(2, '0');
        const centiseconds = Math.floor((ms % 1000) / 10).toString().padStart(2, '0');
        return `${minutes}:${seconds}:${centiseconds}`;
    },

    adjustTimestamp(index, offset) {
        if (this.timestamps[index] !== null) {
            const newTime = Math.round(this.timestamps[index] + offset);
            const duration = Math.round(this.audioPlayer.duration * 1000);

            if (newTime >= 0 && newTime <= duration) {
                // Ensure chronological order
                if (index > 0 && this.timestamps[index - 1] !== null && newTime < this.timestamps[index - 1]) {
                    return;
                }
                if (index < this.words.length - 1 && this.timestamps[index + 1] !== null && newTime > this.timestamps[index + 1]) {
                    return;
                }

                this.timestamps[index] = newTime;
                this.audioPlayer.currentTime = newTime / 1000;
                this.unsavedChanges = true;
            }
        }
        this.updateTimestampDisplay();
    },

    playFromTimestamp(index) {
        if (this.timestamps[index] !== null) {
            this.audioPlayer.currentTime = this.timestamps[index] / 1000;
            this.audioPlayer.play();
        }
    },

    resetStartTime(index) {
        this.timestamps[index] = null;
        this.unsavedChanges = true;
        this.updateActiveLine(Math.max(0, index - 1));
        this.updateTimestampDisplay();
    },

    updateActiveLine(newIndex) {
        const transcriptItems = this.transcriptList.children;

        // Remove active class from previous line
        if (this.activeIndex >= 0 && this.activeIndex < transcriptItems.length) {
            transcriptItems[this.activeIndex].classList.remove('active-line');
        }

        // Add active class to new line
        if (newIndex >= 0 && newIndex < transcriptItems.length) {
            transcriptItems[newIndex].classList.add('active-line');
            this.activeIndex = newIndex;

            // Scroll into view
            transcriptItems[newIndex].scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        } else {
            this.activeIndex = -1;
        }
    },

    updateTimestampDisplay() {
        Array.from(this.transcriptList.children).forEach((item, i) => {
            const timestampInput = item.querySelector('.timestamp');
            if (timestampInput) {
                const hasTime = this.timestamps[i] !== null;
                timestampInput.value = hasTime
                    ? this.formatTime(this.timestamps[i])
                    : '--:--:--';
                timestampInput.classList.toggle('has-time', hasTime);
            }
        });
    },

    handleTimeUpdate() {
        const currentTime = this.audioPlayer.currentTime * 1000;
        let newIndex = -1;

        for (let i = 0; i < this.words.length; i++) {
            if (this.timestamps[i] !== null && currentTime >= this.timestamps[i]) {
                newIndex = i;
            } else if (this.timestamps[i] !== null && currentTime < this.timestamps[i]) {
                break;
            }
        }

        if (newIndex !== this.activeIndex) {
            this.updateActiveLine(newIndex);
        }
    },

    handleKeydown(event) {
        const isInputFocused = document.activeElement.tagName === 'INPUT' && document.activeElement.type === 'text';

        switch (event.key) {
            case ' ':
                if (event.shiftKey) {
                    event.preventDefault();
                    this.audioPlayer.paused ? this.audioPlayer.play() : this.audioPlayer.pause();
                }
                break;

            case 'ArrowDown':
                if (!isInputFocused) {
                    event.preventDefault();
                    if (this.activeIndex < this.words.length - 1) {
                        this.updateActiveLine(this.activeIndex + 1);
                        this.timestamps[this.activeIndex] = Math.round(this.audioPlayer.currentTime * 1000);
                        this.unsavedChanges = true;
                        this.updateTimestampDisplay();
                    }
                }
                break;

            case 'ArrowUp':
                if (!isInputFocused) {
                    event.preventDefault();
                    if (this.activeIndex >= 0) {
                        this.timestamps[this.activeIndex] = null;
                        this.unsavedChanges = true;
                        this.updateActiveLine(this.activeIndex - 1);
                        this.updateTimestampDisplay();
                    }
                }
                break;

            case 'ArrowLeft':
                if (event.shiftKey && !isInputFocused) {
                    event.preventDefault();
                    this.audioPlayer.currentTime = Math.max(this.audioPlayer.currentTime - 1, 0);
                } else if (!isInputFocused && this.activeIndex >= 0) {
                    this.adjustTimestamp(this.activeIndex, -50);
                }
                break;

            case 'ArrowRight':
                if (event.shiftKey && !isInputFocused) {
                    event.preventDefault();
                    this.audioPlayer.currentTime = Math.min(this.audioPlayer.currentTime + 1, this.audioPlayer.duration);
                } else if (!isInputFocused && this.activeIndex >= 0) {
                    this.adjustTimestamp(this.activeIndex, 50);
                }
                break;

            case 's':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.saveAnnotations();
                }
                break;
        }
    },

    openFlagModal(index, flagBtn) {
        const modal = new bootstrap.Modal(document.getElementById('flagModal'));
        modal.show();

        // Populate modal with existing values
        const flagData = this.flags[index] || {};
        document.getElementById('flagComment').value = flagData.comment || '';

        Array.from(document.querySelectorAll('#flagReasons input[type="checkbox"]')).forEach(cb => {
            cb.checked = Array.isArray(flagData.reasons) && flagData.reasons.includes(cb.value);
        });

        // Set up submit handler
        const submitBtn = document.getElementById('submitFlagBtn');
        const newSubmitBtn = submitBtn.cloneNode(true);
        submitBtn.parentNode.replaceChild(newSubmitBtn, submitBtn);

        newSubmitBtn.addEventListener('click', () => {
            const checkboxes = document.querySelectorAll('#flagReasons input[type="checkbox"]:checked');
            const reasons = Array.from(checkboxes).map(cb => cb.value);
            const comment = document.getElementById('flagComment').value;

            if (reasons.length > 0 || comment.trim()) {
                this.flags[index] = { reasons, comment };
                flagBtn.classList.add('flag-active');
                flagBtn.innerHTML = '<i class="bi bi-flag-fill"></i>';
            } else {
                delete this.flags[index];
                flagBtn.classList.remove('flag-active');
                flagBtn.innerHTML = '<i class="bi bi-flag"></i>';
            }

            this.unsavedChanges = true;

            // Reset modal
            Array.from(document.querySelectorAll('#flagReasons input[type="checkbox"]')).forEach(cb => cb.checked = false);
            document.getElementById('flagComment').value = '';
        });
    },

    async saveAnnotations() {
        const annotations = [];

        this.words.forEach((word, index) => {
            annotations.push({
                word_index: index,
                word_text: word,
                timestamp_ms: this.timestamps[index],
                flags: this.flags[index] || null
            });
        });

        try {
            this.showStatus('Saving...', 'info');

            const response = await fetch(`/api/poems/${this.poemId}/annotations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ annotations })
            });

            if (response.ok) {
                this.unsavedChanges = false;
                this.showStatus('Saved successfully!', 'success');
            } else {
                const error = await response.json();
                // Handle both string and array error details (FastAPI validation errors)
                let errorMessage = 'Unknown error';
                if (typeof error.detail === 'string') {
                    errorMessage = error.detail;
                } else if (Array.isArray(error.detail)) {
                    errorMessage = error.detail.map(e => e.msg || JSON.stringify(e)).join(', ');
                } else if (error.detail) {
                    errorMessage = JSON.stringify(error.detail);
                }
                this.showStatus(`Error: ${errorMessage}`, 'danger');
            }
        } catch (error) {
            console.error('Error saving annotations:', error);
            this.showStatus('Error saving annotations', 'danger');
        }
    },

    exportCSV() {
        let csvContent = 'data:text/csv;charset=utf-8,word_index,word,timestamp,flags,comment\n';

        this.words.forEach((word, index) => {
            const timestamp = this.timestamps[index] !== null
                ? this.formatTime(this.timestamps[index])
                : '';
            const wordText = `"${word.replace(/"/g, '""')}"`;
            const flag = this.flags[index];
            const flagStr = flag && Array.isArray(flag.reasons)
                ? `"${flag.reasons.join(';')}"`
                : '';
            const commentStr = flag?.comment
                ? `"${flag.comment.replace(/"/g, '""')}"`
                : '';

            csvContent += `${index},${wordText},${timestamp},${flagStr},${commentStr}\n`;
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.href = encodedUri;
        link.download = `poem_${this.poemId}_annotations.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    showStatus(message, type) {
        if (type === 'success') {
            // Show success modal instead of toast
            const successModalEl = document.getElementById('successModal');
            if (successModalEl) {
                const modal = new bootstrap.Modal(successModalEl);
                modal.show();
                setTimeout(() => modal.hide(), 2000);
            }
        } else if (this.statusMessage) {
            // Keep toast for errors/info
            this.statusMessage.textContent = message;
            this.statusMessage.className = `alert alert-${type}`;
            this.statusMessage.style.display = 'block';

            if (type === 'info') {
                setTimeout(() => {
                    this.statusMessage.style.display = 'none';
                }, 3000);
            }
        }
    }
};

// Export for use in templates
window.LayaAnnotator = LayaAnnotator;
