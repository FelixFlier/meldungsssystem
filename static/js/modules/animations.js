/**
 * Animations Module
 * Handles visual effects, animations, and background elements
 */

/**
 * Creates a star field with animated stars
 */
export function createStarField() {
    const container = document.getElementById('stars-container');
    if (!container) {
        console.warn('Stars container not found!');
        return;
    }
    
    // Force container styling to ensure visibility
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.overflow = 'hidden';
    container.style.pointerEvents = 'none';
    container.style.zIndex = '1';
    
    // Clear existing stars
    container.innerHTML = '';
    
    // Create more stars for better effect
    const numStars = 200;
    for (let i = 0; i < numStars; i++) {
        const star = document.createElement('div');
        
        // Star size with more variety
        if (i % 25 === 0) {
            star.className = 'star extra-large twinkle-drift';
        } else if (i % 15 === 0) {
            star.className = 'star large twinkle';
        } else if (i % 5 === 0) {
            star.className = 'star medium drift';
        } else {
            star.className = 'star small';
            if (i % 3 === 0) {
                star.classList.add('twinkle');
            }
        }
        
        // Explicitly set star styles
        star.style.pointerEvents = 'none';
        star.style.position = 'absolute';
        star.style.borderRadius = '50%';
        star.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
        
        // Set star size
        if (star.classList.contains('extra-large')) {
            star.style.width = '3.5px';
            star.style.height = '3.5px';
            star.style.boxShadow = '0 0 8px 2px rgba(0, 195, 137, 0.6)';
        } else if (star.classList.contains('large')) {
            star.style.width = '2.5px';
            star.style.height = '2.5px';
            star.style.boxShadow = '0 0 5px 2px rgba(0, 195, 137, 0.5)';
        } else if (star.classList.contains('medium')) {
            star.style.width = '1.5px';
            star.style.height = '1.5px';
            star.style.boxShadow = '0 0 3px 1px rgba(0, 195, 137, 0.4)';
        } else {
            star.style.width = '1px';
            star.style.height = '1px';
            star.style.boxShadow = '0 0 2px 1px rgba(0, 195, 137, 0.3)';
        }
        
        // Random position with better distribution
        const x = Math.random() * 100;
        const y = Math.random() * 100;
        star.style.left = `${x}%`;
        star.style.top = `${y}%`;
        
        // Explicitly set animations
        if (star.classList.contains('twinkle')) {
            star.style.animation = 'twinkle 3s ease-in-out infinite';
        }
        
        if (star.classList.contains('drift')) {
            star.style.animation = 'drift 15s ease-in-out infinite';
        }
        
        if (star.classList.contains('twinkle-drift')) {
            star.style.animation = 'twinkle 3s ease-in-out infinite, drift 15s ease-in-out infinite';
        }
        
        // Random animation delay
        star.style.animationDelay = `${Math.random() * 5}s`;
        
        container.appendChild(star);
    }
    
    console.log(`Star field created with ${numStars} stars`);
}

/**
 * Add click ripple effect to buttons
 */
export function addButtonRippleEffect() {
    const buttons = document.querySelectorAll('.creative-btn');
    
    buttons.forEach(button => {
        // Remove existing event listeners to prevent duplicates
        button.removeEventListener('click', handleButtonClick);
        
        // Add the event listener
        button.addEventListener('click', handleButtonClick);
    });
    
    console.log('Button ripple effects added to', buttons.length, 'buttons');
}

/**
 * Button click handler for ripple effect
 * @param {Event} e Click event
 */
function handleButtonClick(e) {
    const button = e.currentTarget;
    
    // Get button position
    const rect = button.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Create ripple element
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.position = 'absolute';
    ripple.style.borderRadius = '50%';
    ripple.style.transform = 'scale(0)';
    ripple.style.animation = 'ripple 0.6s linear';
    ripple.style.backgroundColor = 'rgba(255, 255, 255, 0.7)';
    
    // Position the ripple
    ripple.style.width = '100px';
    ripple.style.height = '100px';
    ripple.style.left = x - 50 + 'px';
    ripple.style.top = y - 50 + 'px';
    
    // Add and clean up
    button.appendChild(ripple);
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

/**
 * Make all interactive elements more accessible with animation
 */
export function enhanceInteractiveElements() {
    // Make buttons and links more clickable
    const clickableElements = document.querySelectorAll('button, a, [data-action], .card');
    
    clickableElements.forEach(element => {
        // Ensure proper styling for clickability
        element.style.position = 'relative';
        element.style.zIndex = '20';
        element.style.cursor = 'pointer';
        
        // Add hover animation (but check if already processed)
        if (!element.classList.contains('hover-animation-processed')) {
            element.classList.add('hover-animation-processed');
            
            element.addEventListener('mouseenter', function() {
                this.classList.add('hover-animation');
            });
            
            element.addEventListener('mouseleave', function() {
                this.classList.remove('hover-animation');
            });
        }
    });
    
    // Ensure overlays don't catch clicks
    const overlays = document.querySelectorAll('.green-glow-overlay, #stars-container');
    overlays.forEach(overlay => {
        overlay.style.pointerEvents = 'none';
    });
    
    console.log('Interactive elements enhanced');
}

/**
 * Ensure all required CSS animations are available
 */
function ensureAnimationStyles() {
    // Add CSS for ripple effect if not present
    if (!document.getElementById('animation-styles')) {
        const style = document.createElement('style');
        style.id = 'animation-styles';
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
            
            .hover-animation {
                transform: translateY(-2px);
                transition: transform 0.3s ease;
            }
            
            /* In case twinkle/drift animations are missing */
            @keyframes twinkle {
                0%, 100% { opacity: 0.15; }
                50% { opacity: 0.8; }
            }
            
            @keyframes drift {
                0% { transform: translate(0, 0); }
                25% { transform: translate(5px, 5px); }
                50% { transform: translate(0, 10px); }
                75% { transform: translate(-5px, 5px); }
                100% { transform: translate(0, 0); }
            }
        `;
        document.head.appendChild(style);
        console.log('Animation styles added to document');
    }
}

/**
 * Initialize all animations
 */
export function initAnimations() {
    console.log('Initializing animations');
    
    // Ensure all animation styles are available
    ensureAnimationStyles();
    
    // Create star field background
    createStarField();
    
    // Add button effects
    addButtonRippleEffect();
    
    // Enhance interactive elements
    enhanceInteractiveElements();
    
    console.log('Animations initialized');
}

export default {
    createStarField,
    addButtonRippleEffect,
    enhanceInteractiveElements,
    initAnimations
};