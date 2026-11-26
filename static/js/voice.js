/**
 * Web Speech API Voice Recognition Service
 * Supports en-IN (English - India) and hi-IN (Hindi)
 * Client-side only; does not upload or retain raw audio recordings.
 */

class VoiceInputController {
    constructor() {
        this.recognition = null;
        this.isRecording = false;
        this.currentTargetInput = null;
        this.currentStatusElement = null;
        this.currentMicButton = null;
        this.selectedLanguage = 'en-IN'; // default English (India)
        this.hasSpeechSupport = false;

        this.init();
    }

    init() {
        // Detect browser SpeechRecognition support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = this.selectedLanguage;
            this.hasSpeechSupport = true;

            this.setupEventHandlers();
        } else {
            console.warn('Web Speech API is not supported in this browser. Falling back to keyboard text input.');
        }
    }

    setupEventHandlers() {
        if (!this.recognition) return;

        this.recognition.onstart = () => {
            this.isRecording = true;
            this.updateUIState(true);
            if (this.currentStatusElement) {
                this.currentStatusElement.innerHTML = `<span class="text-danger fw-bold"><i class="fa-solid fa-circle-dot fa-fade me-1"></i> Listening in ${this.getLanguageLabel()}... Speak now</span>`;
            }
        };

        this.recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            if (this.currentTargetInput) {
                // If final text was recognized, append or update
                if (finalTranscript) {
                    const existing = this.currentTargetInput.value.trim();
                    this.currentTargetInput.value = existing ? `${existing} ${finalTranscript}` : finalTranscript;
                    // Trigger input event for real-time AI listeners
                    this.currentTargetInput.dispatchEvent(new Event('input', { bubbles: true }));
                }
                
                if (interimTranscript && this.currentStatusElement) {
                    this.currentStatusElement.innerHTML = `<span class="text-primary"><i class="fa-solid fa-waveform-lines fa-fade me-1"></i> "${interimTranscript}"</span>`;
                }
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            let message = 'Voice error occurred.';
            if (event.error === 'not-allowed') {
                message = 'Microphone permission was denied. Please allow microphone access in your browser settings to use voice input.';
            } else if (event.error === 'no-speech') {
                message = 'No speech was detected. Please try speaking closer to the microphone.';
            } else if (event.error === 'network') {
                message = 'Network connectivity required for voice recognition services.';
            }
            if (this.currentStatusElement) {
                this.currentStatusElement.innerHTML = `<span class="text-warning"><i class="fa-solid fa-triangle-exclamation me-1"></i> ${message}</span>`;
            }
            this.stop();
        };

        this.recognition.onend = () => {
            this.isRecording = false;
            this.updateUIState(false);
            if (this.currentStatusElement && !this.currentStatusElement.innerHTML.includes('text-warning')) {
                this.currentStatusElement.innerHTML = `<span class="text-success"><i class="fa-solid fa-circle-check me-1"></i> Voice converted to text. You can review and edit above.</span>`;
            }
        };
    }

    setLanguage(langCode) {
        this.selectedLanguage = langCode;
        if (this.recognition) {
            this.recognition.lang = langCode;
        }
    }

    getLanguageLabel() {
        return this.selectedLanguage === 'hi-IN' ? 'Hindi (हिन्दी)' : 'English (India)';
    }

    toggle(targetInputId, statusElementId, buttonElement) {
        if (!this.hasSpeechSupport) {
            alert('Voice input is not supported in this browser version. You can still type directly into the text field.');
            return;
        }

        if (this.isRecording) {
            this.stop();
        } else {
            this.start(targetInputId, statusElementId, buttonElement);
        }
    }

    start(targetInputId, statusElementId, buttonElement) {
        this.currentTargetInput = document.getElementById(targetInputId);
        this.currentStatusElement = document.getElementById(statusElementId);
        this.currentMicButton = buttonElement;

        try {
            this.recognition.start();
        } catch (e) {
            console.warn('Recognition already started or error:', e);
        }
    }

    stop() {
        if (this.recognition && this.isRecording) {
            try {
                this.recognition.stop();
            } catch (e) {}
        }
        this.isRecording = false;
        this.updateUIState(false);
    }

    updateUIState(isRecording) {
        if (this.currentMicButton) {
            if (isRecording) {
                this.currentMicButton.classList.add('recording');
                this.currentMicButton.innerHTML = `<i class="fa-solid fa-stop me-1"></i> Stop Recording`;
            } else {
                this.currentMicButton.classList.remove('recording');
                this.currentMicButton.innerHTML = `<i class="fa-solid fa-microphone me-1"></i> Speak Symptoms`;
            }
        }
    }
}

// Global voice controller instance
window.voiceController = new VoiceInputController();
