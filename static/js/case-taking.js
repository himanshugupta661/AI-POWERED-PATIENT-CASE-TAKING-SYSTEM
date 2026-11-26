/**
 * Case-Taking Wizard Controller - PatientCase AI
 * Controls multi-step tabs, symptom text listening, and follow-up pagination.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Live AI analysis on symptoms text change
    const symptomsTextarea = document.getElementById('intake_symptoms');
    if (symptomsTextarea && window.aiExtractor) {
        symptomsTextarea.addEventListener('input', (e) => {
            window.aiExtractor.debounceAnalyze(e.target.value);
        });
    }

    // Manual 'Analyze with AI' button
    const btnTriggerAI = document.getElementById('btnTriggerAI');
    if (btnTriggerAI && symptomsTextarea && window.aiExtractor) {
        btnTriggerAI.addEventListener('click', () => {
            window.aiExtractor.analyzeText(symptomsTextarea.value, true);
        });
    }

    // 2. Prevent duplicate form submissions
    const caseForm = document.getElementById('patientCaseForm');
    if (caseForm) {
        caseForm.addEventListener('submit', () => {
            const submitBtn = caseForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-2"></i> Saving Case...`;
            }
        });
    }

    // 3. Follow-up Questions Pagination Logic (Question X of Y)
    const questionCards = document.querySelectorAll('.followup-question-card');
    if (questionCards.length > 0) {
        let currentQIndex = 0;
        const totalQuestions = questionCards.length;
        const counterDisplay = document.getElementById('followupCounter');
        const progressBar = document.getElementById('followupProgressBar');
        const btnPrevQ = document.getElementById('btnPrevQuestion');
        const btnNextQ = document.getElementById('btnNextQuestion');
        const btnSubmitFollowup = document.getElementById('btnSubmitFollowup');

        function showQuestion(index) {
            questionCards.forEach((card, idx) => {
                if (idx === index) {
                    card.classList.remove('d-none');
                } else {
                    card.classList.add('d-none');
                }
            });

            if (counterDisplay) {
                counterDisplay.textContent = `Question ${index + 1} of ${totalQuestions}`;
            }

            if (progressBar) {
                const percent = Math.round(((index + 1) / totalQuestions) * 100);
                progressBar.style.width = `${percent}%`;
            }

            if (btnPrevQ) {
                btnPrevQ.disabled = (index === 0);
            }

            if (index === totalQuestions - 1) {
                if (btnNextQ) btnNextQ.classList.add('d-none');
                if (btnSubmitFollowup) btnSubmitFollowup.classList.remove('d-none');
            } else {
                if (btnNextQ) btnNextQ.classList.remove('d-none');
                if (btnSubmitFollowup) btnSubmitFollowup.classList.add('d-none');
            }
        }

        if (btnNextQ) {
            btnNextQ.addEventListener('click', () => {
                if (currentQIndex < totalQuestions - 1) {
                    currentQIndex++;
                    showQuestion(currentQIndex);
                }
            });
        }

        if (btnPrevQ) {
            btnPrevQ.addEventListener('click', () => {
                if (currentQIndex > 0) {
                    currentQIndex--;
                    showQuestion(currentQIndex);
                }
            });
        }

        // Initialize question viewer
        showQuestion(0);
    }
});
