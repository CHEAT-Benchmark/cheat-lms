/**
 * Client-side telemetry for CHEAT LMS
 * Tracks user interactions and timing data for AI detection
 */

(function() {
    'use strict';

    const Telemetry = {
        sessionId: null,
        pageLoadTime: Date.now(),
        interactions: [],
        firstInteractionTracked: false,
        lastClickTime: null,
        lastScrollTime: null,
        questionTimings: {},  // questionId -> { focusedAt, answeredAt }
        flushInterval: null,
        FLUSH_INTERVAL_MS: 5000,
        SCROLL_DEBOUNCE_MS: 100,

        init: function() {
            this.sessionId = this.getOrCreateSessionId();
            this.trackPageLoad();
            this.setupEventListeners();
            this.startPeriodicFlush();
        },

        getOrCreateSessionId: function() {
            let sessionId = sessionStorage.getItem('telemetry_session_id');
            if (!sessionId) {
                sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                sessionStorage.setItem('telemetry_session_id', sessionId);
            }
            return sessionId;
        },

        getAssignmentId: function() {
            // Extract assignment ID from URL like /assignment/123
            const match = window.location.pathname.match(/\/assignment\/(\d+)/);
            return match ? parseInt(match[1], 10) : null;
        },

        trackPageLoad: function() {
            this.logEvent('page_load', {
                url: window.location.href,
                path: window.location.pathname,
                referrer: document.referrer,
                userAgent: navigator.userAgent,
                screenWidth: window.screen.width,
                screenHeight: window.screen.height,
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight,
                timestamp: new Date().toISOString()
            });
        },

        trackFirstInteraction: function(interactionType) {
            if (this.firstInteractionTracked) return;
            this.firstInteractionTracked = true;

            const timeSinceLoad = Date.now() - this.pageLoadTime;
            this.logEvent('first_interaction', {
                interactionType: interactionType,
                timeSinceLoadMs: timeSinceLoad,
                assignmentId: this.getAssignmentId()
            });
        },

        setupEventListeners: function() {
            const self = this;

            // Track first interaction (click, keystroke, or scroll)
            const firstInteractionHandler = function(e) {
                self.trackFirstInteraction(e.type);
            };
            document.addEventListener('click', firstInteractionHandler, { once: true });
            document.addEventListener('keydown', firstInteractionHandler, { once: true });
            document.addEventListener('scroll', firstInteractionHandler, { once: true });

            // Track all clicks with position and timing
            document.addEventListener('click', function(e) {
                const now = Date.now();
                const timeSincePrevClick = self.lastClickTime ? now - self.lastClickTime : null;
                self.lastClickTime = now;

                self.logEvent('click', {
                    x: e.clientX,
                    y: e.clientY,
                    pageX: e.pageX,
                    pageY: e.pageY,
                    target: e.target.tagName,
                    targetId: e.target.id || null,
                    targetClass: e.target.className || null,
                    timeSincePrevClickMs: timeSincePrevClick,
                    timeOnPage: now - self.pageLoadTime,
                    assignmentId: self.getAssignmentId()
                });
            });

            // Track scroll events (debounced)
            let scrollTimeout = null;
            document.addEventListener('scroll', function() {
                if (scrollTimeout) return;
                scrollTimeout = setTimeout(function() {
                    const now = Date.now();
                    const timeSincePrevScroll = self.lastScrollTime ? now - self.lastScrollTime : null;
                    self.lastScrollTime = now;

                    self.logEvent('scroll', {
                        scrollY: window.scrollY,
                        scrollX: window.scrollX,
                        maxScrollY: document.documentElement.scrollHeight - window.innerHeight,
                        timeSincePrevScrollMs: timeSincePrevScroll,
                        timeOnPage: now - self.pageLoadTime,
                        assignmentId: self.getAssignmentId()
                    });
                    scrollTimeout = null;
                }, self.SCROLL_DEBOUNCE_MS);
            });

            // Track form submissions
            document.addEventListener('submit', function(e) {
                const form = e.target;

                // Update question timings hidden field before submit
                const timingsField = document.getElementById('question_timings');
                if (timingsField) {
                    timingsField.value = JSON.stringify(self.questionTimings);
                }

                self.logEvent('form_submit', {
                    formAction: form.action,
                    formMethod: form.method,
                    formId: form.id,
                    timeOnPage: Date.now() - self.pageLoadTime,
                    assignmentId: self.getAssignmentId()
                });

                // Flush before navigation
                self.flush();
            });

            // Track quiz question focus and answer events
            document.querySelectorAll('.ic-Question').forEach(function(questionEl, index) {
                const inputs = questionEl.querySelectorAll('input[type="radio"]');
                if (inputs.length === 0) return;

                // Get question ID from input name (e.g., "question_123")
                const inputName = inputs[0].name;
                const questionIdMatch = inputName.match(/question_(\d+)/);
                const questionId = questionIdMatch ? questionIdMatch[1] : index.toString();

                // Track when question becomes visible (focus approximation via IntersectionObserver)
                const observer = new IntersectionObserver(function(entries) {
                    entries.forEach(function(entry) {
                        if (entry.isIntersecting && !self.questionTimings[questionId]) {
                            const now = Date.now();
                            self.questionTimings[questionId] = { focusedAt: now, answeredAt: null };

                            self.logEvent('question_focus', {
                                questionId: questionId,
                                questionIndex: index,
                                timeOnPage: now - self.pageLoadTime,
                                assignmentId: self.getAssignmentId()
                            });
                        }
                    });
                }, { threshold: 0.5 });

                observer.observe(questionEl);

                // Track answer selection
                inputs.forEach(function(input) {
                    input.addEventListener('change', function() {
                        const now = Date.now();

                        // Ensure we have a focus time
                        if (!self.questionTimings[questionId]) {
                            self.questionTimings[questionId] = { focusedAt: now, answeredAt: null };
                        }
                        self.questionTimings[questionId].answeredAt = now;

                        const focusedAt = self.questionTimings[questionId].focusedAt;
                        const timeToAnswer = now - focusedAt;

                        self.logEvent('question_answer', {
                            questionId: questionId,
                            questionIndex: index,
                            selectedValue: input.value,
                            timeToAnswerMs: timeToAnswer,
                            timeOnPage: now - self.pageLoadTime,
                            assignmentId: self.getAssignmentId()
                        });
                    });
                });
            });

            // Also track legacy quiz answer selection for compatibility
            document.querySelectorAll('.ic-Question__choice input').forEach(function(input) {
                input.addEventListener('change', function() {
                    self.logEvent('quiz_answer_selected', {
                        questionId: this.name,
                        selectedValue: this.value,
                        timeOnPage: Date.now() - self.pageLoadTime
                    });
                });
            });

            // Track text input focus/blur for timing and typing velocity
            document.querySelectorAll('textarea').forEach(function(textarea) {
                let focusTime = null;
                let lastInputTime = null;
                let charCount = 0;
                let inputTimes = [];

                textarea.addEventListener('focus', function() {
                    focusTime = Date.now();
                    charCount = this.value.length;
                    inputTimes = [];
                    self.logEvent('textarea_focus', {
                        textareaName: this.name,
                        timeOnPage: Date.now() - self.pageLoadTime
                    });
                });

                textarea.addEventListener('input', function() {
                    const now = Date.now();
                    const newLength = this.value.length;
                    const charsAdded = newLength - charCount;

                    // Detect paste or rapid typing (typing burst)
                    if (charsAdded > 5) {
                        const timeSinceLastInput = lastInputTime ? now - lastInputTime : null;
                        const charsPerSecond = timeSinceLastInput ? (charsAdded / timeSinceLastInput) * 1000 : null;

                        self.logEvent('typing_burst', {
                            textareaName: textarea.name,
                            charsAdded: charsAdded,
                            timeSinceLastInputMs: timeSinceLastInput,
                            charsPerSecond: charsPerSecond,
                            likelyPaste: charsAdded > 20,
                            timeOnPage: now - self.pageLoadTime,
                            assignmentId: self.getAssignmentId()
                        });
                    }

                    inputTimes.push({ time: now, chars: charsAdded });
                    charCount = newLength;
                    lastInputTime = now;
                });

                textarea.addEventListener('blur', function() {
                    const editTime = focusTime ? Date.now() - focusTime : null;

                    // Calculate typing velocity
                    let avgCharsPerSecond = null;
                    if (inputTimes.length > 1) {
                        const totalTime = inputTimes[inputTimes.length - 1].time - inputTimes[0].time;
                        const totalChars = inputTimes.reduce((sum, i) => sum + Math.abs(i.chars), 0);
                        if (totalTime > 0) {
                            avgCharsPerSecond = (totalChars / totalTime) * 1000;
                        }
                    }

                    self.logEvent('textarea_blur', {
                        textareaName: this.name,
                        editTimeMs: editTime,
                        characterCount: this.value.length,
                        wordCount: this.value.trim() ? this.value.trim().split(/\s+/).length : 0,
                        avgCharsPerSecond: avgCharsPerSecond,
                        timeOnPage: Date.now() - self.pageLoadTime
                    });
                });
            });

            // Track clicks on assignment links
            document.querySelectorAll('.ic-AssignmentList__link').forEach(function(link) {
                link.addEventListener('click', function() {
                    self.logEvent('assignment_click', {
                        href: this.href,
                        title: this.querySelector('.ic-AssignmentList__title')?.textContent,
                        timeOnPage: Date.now() - self.pageLoadTime
                    });
                });
            });

            // Track page visibility changes
            document.addEventListener('visibilitychange', function() {
                self.logEvent('visibility_change', {
                    hidden: document.hidden,
                    timeOnPage: Date.now() - self.pageLoadTime,
                    assignmentId: self.getAssignmentId()
                });
            });

            // Track before unload - use sendBeacon for reliable delivery
            window.addEventListener('beforeunload', function() {
                self.logEvent('page_unload', {
                    totalTimeOnPage: Date.now() - self.pageLoadTime,
                    interactionCount: self.interactions.length,
                    assignmentId: self.getAssignmentId()
                });
                // Use sendBeacon for reliable delivery on page unload
                self.flushWithBeacon();
            });
        },

        startPeriodicFlush: function() {
            const self = this;
            this.flushInterval = setInterval(function() {
                if (self.interactions.length > 0) {
                    self.flush();
                }
            }, this.FLUSH_INTERVAL_MS);
        },

        logEvent: function(eventType, data) {
            const event = {
                eventType: eventType,
                sessionId: this.sessionId,
                timestamp: Date.now(),
                data: data
            };
            this.interactions.push(event);

            // Log to console in development
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                console.log('[Telemetry]', eventType, data);
            }
        },

        flush: function() {
            if (this.interactions.length === 0) return;

            const events = this.interactions.slice();
            this.interactions = [];

            // Send to server
            fetch('/api/telemetry/events', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ events: events }),
                credentials: 'same-origin'
            }).catch(function(err) {
                console.error('[Telemetry] Failed to send events:', err);
                // Re-add events on failure (but cap at 1000 to prevent memory issues)
                Telemetry.interactions = events.concat(Telemetry.interactions).slice(-1000);
            });

            // Also store in sessionStorage as backup
            try {
                const existing = JSON.parse(sessionStorage.getItem('telemetry_events') || '[]');
                const combined = existing.concat(events);
                sessionStorage.setItem('telemetry_events', JSON.stringify(combined.slice(-1000)));
            } catch (e) {
                console.error('[Telemetry] Failed to store backup:', e);
            }
        },

        flushWithBeacon: function() {
            if (this.interactions.length === 0) return;

            const events = this.interactions.slice();
            this.interactions = [];

            // Use sendBeacon for reliable delivery on page unload
            const blob = new Blob([JSON.stringify({ events: events })], { type: 'application/json' });
            navigator.sendBeacon('/api/telemetry/events', blob);

            // Also store in sessionStorage as backup
            try {
                const existing = JSON.parse(sessionStorage.getItem('telemetry_events') || '[]');
                const combined = existing.concat(events);
                sessionStorage.setItem('telemetry_events', JSON.stringify(combined.slice(-1000)));
            } catch (e) {
                // Ignore errors on unload
            }
        },

        // Get question timings for form submission
        getQuestionTimings: function() {
            return this.questionTimings;
        }
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            Telemetry.init();
        });
    } else {
        Telemetry.init();
    }

    // Expose for debugging and form submission
    window.CheatTelemetry = Telemetry;
})();
