class MobileMenu {
  constructor() {
    this.menu = document.querySelector('.left-side');
    this.overlay = document.querySelector('.menu-overlay');
    this.hamburger = document.querySelector('.hamburger-menu');
    this.pageContainer = document.querySelector('.page-container');
    this.touchStartX = 0;
    this.touchEndX = 0;
    this.currentX = 0;
    this.isDragging = false;
    
    this.init();
  }
  
  init() {
    // Create and append overlay if it doesn't exist
    if (!this.overlay) {
      this.overlay = document.createElement('div');
      this.overlay.className = 'menu-overlay';
      document.body.appendChild(this.overlay);
    }

    // Create and append hamburger if it doesn't exist
    if (!this.hamburger) {
      this.hamburger = document.createElement('button');
      this.hamburger.className = 'hamburger-menu';
      this.hamburger.innerHTML = '☰';
      document.body.appendChild(this.hamburger);
    }

    // Toggle menu
    this.hamburger.addEventListener('click', () => this.toggleMenu());
    
    // Click outside to close
    this.overlay.addEventListener('click', () => this.closeMenu());
    
    // Touch events for the menu
    this.menu.addEventListener('touchstart', (e) => this.handleTouchStart(e));
    this.menu.addEventListener('touchmove', (e) => this.handleTouchMove(e));
    this.menu.addEventListener('touchend', (e) => this.handleTouchEnd(e));

    // Edge swipe to open
    document.addEventListener('touchstart', (e) => {
      if (e.touches[0].clientX < 30 && !this.isMenuActive()) {
        this.handleEdgeSwipe(e);
      }
    });

    // Handle escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isMenuActive()) {
        this.closeMenu();
      }
    });

    // Handle window resize
    window.addEventListener('resize', () => this.handleResize());
  }

  handleEdgeSwipe(e) {
    this.touchStartX = e.touches[0].clientX;
    this.isDragging = true;
    
    const handleMove = (e) => {
      if (!this.isDragging) return;
      
      const touch = e.touches[0];
      const diff = touch.clientX - this.touchStartX;
      
      if (diff > 0 && diff <= 280) {
        this.menu.style.transform = `translateX(${diff}px)`;
        this.overlay.style.display = 'block';
        this.overlay.style.opacity = diff / 280 * 0.5;
      }
    };
    
    const handleEnd = (e) => {
      this.isDragging = false;
      const diff = e.changedTouches[0].clientX - this.touchStartX;
      
      if (diff > 100) {
        this.openMenu();
      } else {
        this.closeMenu();
      }
      
      document.removeEventListener('touchmove', handleMove);
      document.removeEventListener('touchend', handleEnd);
    };
    
    document.addEventListener('touchmove', handleMove);
    document.addEventListener('touchend', handleEnd);
  }

  handleTouchStart(e) {
    if (!this.isMenuActive()) return;
    this.touchStartX = e.touches[0].clientX;
    this.currentX = 0;
    this.isDragging = true;
  }

  handleTouchMove(e) {
    if (!this.isDragging) return;
    
    const touch = e.touches[0];
    const diff = this.touchStartX - touch.clientX;
    
    if (diff > 0) {
      e.preventDefault();
      this.currentX = -diff;
      this.menu.style.transform = `translateX(${280 + this.currentX}px)`;
      this.overlay.style.opacity = (280 + this.currentX) / 280 * 0.5;
    }
  }

  handleTouchEnd(e) {
    if (!this.isDragging) return;
    
    this.isDragging = false;
    this.touchEndX = e.changedTouches[0].clientX;
    const diff = this.touchStartX - this.touchEndX;
    
    if (diff > 100) { // Threshold for closing
      this.closeMenu();
    } else {
      this.openMenu();
    }
  }

  handleResize() {
    if (window.innerWidth > 768 && this.isMenuActive()) {
      this.closeMenu();
    }
  }

  isMenuActive() {
    return this.menu.classList.contains('active');
  }

  toggleMenu() {
    if (this.isMenuActive()) {
      this.closeMenu();
    } else {
      this.openMenu();
    }
  }
  
  openMenu() {
    this.menu.classList.add('active');
    this.overlay.classList.add('active');
    this.pageContainer.classList.add('menu-active');
    this.menu.style.transform = '';
    document.body.style.overflow = 'hidden';
  }
  
  closeMenu() {
    this.menu.classList.remove('active');
    this.overlay.classList.remove('active');
    this.pageContainer.classList.remove('menu-active');
    this.menu.style.transform = '';
    document.body.style.overflow = '';
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new MobileMenu();
});
