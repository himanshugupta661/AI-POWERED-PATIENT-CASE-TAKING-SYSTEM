/**
 * PatientCase AI Client Service
 * Interacts with backend rule-based NLP extraction endpoint
 * Provides instant preliminary extraction feedback to patient
 */

class AISymptomExtractor {
    constructor() {
        this.debounceTimer = null;
    }

    async analyzeText(text, updateFormFields = true) {
        if (!text || text.trim().length < 5) return null;

        const previewContainer = document.getElementById('aiExtractionPreview');
        const previewTags = document.getElementById('aiDetectedSymptoms');
        const loadingIndicator = document.getElementById('aiLoadingIndicator');

        if (loadingIndicator) loadingIndicator.classList.remove('d-none');

        try {
            const response = await fetch('/api/extract-symptoms', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text })
            });

            if (!response.ok) throw new Error('Extraction request failed');

            const result = await response.json();
            if (result.success && result.data) {
                const data = result.data;

                // Render detected symptoms chips
                if (previewContainer && previewTags) {
                    previewContainer.classList.remove('d-none');
                    if (data.detected_symptoms && data.detected_symptoms.length > 0) {
                        previewTags.innerHTML = data.detected_symptoms.map(s => 
                            `<span class="ai-tag-pill"><i class="fa-solid fa-stethoscope"></i> ${s}</span>`
                        ).join('');
                    } else {
                        previewTags.innerHTML = `<span class="text-muted small">General symptoms recorded. Review details below.</span>`;
                    }
                }

                // Auto-fill form fields if enabled and field is currently empty
                if (updateFormFields) {
                    const durationInput = document.getElementById('intake_duration');
                    if (durationInput && !durationInput.value.trim() && data.duration) {
                        durationInput.value = data.duration;
                        durationInput.classList.add('border-primary');
                    }

                    const severityInput = document.getElementById('intake_severity');
                    if (severityInput && !severityInput.value.trim() && data.severity) {
                        severityInput.value = data.severity;
                        severityInput.classList.add('border-primary');
                    }

                    const patternInput = document.getElementById('intake_pattern');
                    if (patternInput && !patternInput.value.trim() && data.pattern) {
                        patternInput.value = data.pattern;
                        patternInput.classList.add('border-primary');
                    }

                    const complaintInput = document.getElementById('intake_chief_complaint');
                    if (complaintInput && !complaintInput.value.trim() && data.chief_complaint) {
                        complaintInput.value = data.chief_complaint;
                    }
                }

                return data;
            }
        } catch (err) {
            console.warn('AI Extraction notice:', err);
        } finally {
            if (loadingIndicator) loadingIndicator.classList.add('d-none');
        }
        return null;
    }

    debounceAnalyze(text, delayMs = 1200) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.analyzeText(text, true);
        }, delayMs);
    }
}

window.aiExtractor = new AISymptomExtractor();
