document.addEventListener('DOMContentLoaded', () => {
    const animated = document.querySelector('[data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"]');

    if (animated) {
        // Add the animation class to start the glow animation
        animated.classList.add('animate-glow');

        // After a certain duration, remove the animation class to stop the glow
        setTimeout(() => {
            animated.classList.remove('animate-glow');
        }, 3000); // Change the duration as needed (3000ms = 3 seconds)
    }
});