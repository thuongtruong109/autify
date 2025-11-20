// Mobile menu toggle
const mobileMenuToggle = document.querySelector(".mobile-menu-toggle");
const navLinks = document.querySelector(".nav-links");

if (mobileMenuToggle) {
  mobileMenuToggle.addEventListener("click", () => {
    mobileMenuToggle.classList.toggle("active");
    navLinks.classList.toggle("active");
  });

  // Close menu when clicking on a link
  document.querySelectorAll(".nav-links a").forEach((link) => {
    link.addEventListener("click", () => {
      mobileMenuToggle.classList.remove("active");
      navLinks.classList.remove("active");
    });
  });

  // Close menu when clicking outside
  document.addEventListener("click", (e) => {
    if (!mobileMenuToggle.contains(e.target) && !navLinks.contains(e.target)) {
      mobileMenuToggle.classList.remove("active");
      navLinks.classList.remove("active");
    }
  });
}

// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      const offset = 80;
      const elementPosition = target.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - offset;

      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth",
      });
    }
  });
});

// Navbar scroll effect
let lastScroll = 0;
const navbar = document.querySelector(".navbar");

window.addEventListener("scroll", () => {
  const currentScroll = window.pageYOffset;

  if (currentScroll > 100) {
    navbar.style.boxShadow = "var(--shadow-md)";
  } else {
    navbar.style.boxShadow = "none";
  }

  lastScroll = currentScroll;
});

// Intersection Observer for fade-in animations
const observerOptions = {
  threshold: 0.1,
  rootMargin: "0px 0px -100px 0px",
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = "1";
      entry.target.style.transform = "translateY(0)";
    }
  });
}, observerOptions);

// Observe all cards and sections
document
  .querySelectorAll(".feature-card, .module-card, .doc-card, .tech-item")
  .forEach((el) => {
    el.style.opacity = "0";
    el.style.transform = "translateY(30px)";
    el.style.transition = "opacity 0.6s ease, transform 0.6s ease";
    observer.observe(el);
  });

// Copy code block functionality
document.querySelectorAll(".code-block").forEach((block) => {
  block.style.position = "relative";
  block.style.cursor = "pointer";

  block.addEventListener("click", () => {
    const code = block.textContent;
    navigator.clipboard.writeText(code).then(() => {
      // Create and show tooltip
      const tooltip = document.createElement("div");
      tooltip.textContent = "Copied!";
      tooltip.style.cssText = `
                position: absolute;
                top: 8px;
                right: 8px;
                background: var(--primary);
                color: white;
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                pointer-events: none;
                animation: fadeIn 0.3s ease;
            `;
      block.appendChild(tooltip);

      setTimeout(() => {
        tooltip.remove();
      }, 2000);
    });
  });
});

// Add hover effect to module cards
document.querySelectorAll(".module-card").forEach((card) => {
  card.addEventListener("mouseenter", function () {
    this.style.borderColor = "var(--primary)";
  });

  card.addEventListener("mouseleave", function () {
    this.style.borderColor = "var(--border)";
  });
});

// Parallax effect for hero gradient
window.addEventListener("scroll", () => {
  const heroGradient = document.querySelector(".hero-gradient");
  if (heroGradient) {
    const scrolled = window.pageYOffset;
    heroGradient.style.transform = `translateX(-50%) translateY(${
      scrolled * 0.3
    }px)`;
  }
});

// Add loading state to buttons
document
  .querySelectorAll(".btn-primary, .btn-secondary, .btn-outline")
  .forEach((btn) => {
    btn.addEventListener("click", function (e) {
      if (this.href && !this.href.includes("#")) {
        // Add ripple effect
        const ripple = document.createElement("span");
        ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.6);
                width: 100px;
                height: 100px;
                margin-top: -50px;
                margin-left: -50px;
                animation: ripple 0.6s;
                pointer-events: none;
            `;

        const rect = this.getBoundingClientRect();
        ripple.style.left = e.clientX - rect.left + "px";
        ripple.style.top = e.clientY - rect.top + "px";

        this.appendChild(ripple);

        setTimeout(() => {
          ripple.remove();
        }, 600);
      }
    });
  });

// Add ripple animation to CSS dynamically
const style = document.createElement("style");
style.textContent = `
    @keyframes ripple {
        from {
            opacity: 1;
            transform: scale(0);
        }
        to {
            opacity: 0;
            transform: scale(4);
        }
    }

    .btn-primary, .btn-secondary, .btn-outline, .btn-large {
        position: relative;
        overflow: hidden;
    }
`;
document.head.appendChild(style);

// Stats counter animation
const animateCounter = (element, target) => {
  let current = 0;
  const increment = target / 50;
  const timer = setInterval(() => {
    current += increment;
    if (current >= target) {
      element.textContent = target;
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(current);
    }
  }, 30);
};

// Observe stats section
const statsObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const statValues = entry.target.querySelectorAll(".stat-value");
        statValues.forEach((stat) => {
          const text = stat.textContent;
          const number = parseInt(text);
          if (!isNaN(number)) {
            animateCounter(stat, number);
          }
        });
        statsObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.5 }
);

const heroStats = document.querySelector(".hero-stats");
if (heroStats) {
  statsObserver.observe(heroStats);
}

// Add active state to navigation
const sections = document.querySelectorAll("section[id]");
const navLinksItems = document.querySelectorAll(".nav-links a");

window.addEventListener("scroll", () => {
  let current = "";

  sections.forEach((section) => {
    const sectionTop = section.offsetTop;
    const sectionHeight = section.clientHeight;
    if (pageYOffset >= sectionTop - 100) {
      current = section.getAttribute("id");
    }
  });

  navLinksItems.forEach((link) => {
    link.classList.remove("active");
    // Only add active if current is not empty and matches exactly
    if (current && link.getAttribute("href") === `#${current}`) {
      link.classList.add("active");
    }
  });
});

// Add active link style
const activeLinkStyle = document.createElement("style");
activeLinkStyle.textContent = `
    .nav-links a.active {
        color: var(--primary);
        position: relative;
    }

    .nav-links a.active::after {
        content: '';
        position: absolute;
        bottom: -8px;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--primary);
        border-radius: 2px;
    }
`;
document.head.appendChild(activeLinkStyle);

console.log("🚀 Autify Landing Page Loaded Successfully!");
