# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal portfolio/resume website built using the MyResume template from BootstrapMade. It's a static HTML website showcasing Hadi Mohammadi's professional profile, projects, publications, and academic work.

## Architecture

The website follows a traditional static site structure:

- **HTML Pages**: 
  - `index.html` - Main landing page with hero section, about, resume, and contact sections
  - `Projects.html`, `Publications.html`, `Cooperation.html` - Additional content pages
  - `book.html`, `presentations.html`, `teaching.html` - Academic content pages
  - `portfolio-details.html`, `service-details.html` - Detail view templates

- **Assets Organization**:
  - `assets/css/` - Stylesheets (main.css, style.css, book.css)
  - `assets/js/` - JavaScript files (main.js handles interactions)
  - `assets/img/` - Images, certificates, organization logos
  - `assets/docs/` - PDFs for CV, publications, presentations, project images
  - `assets/vendor/` - Third-party libraries (Bootstrap, AOS, Glightbox, etc.)

- **Forms**: PHP contact form handler (requires server-side setup)

## Key Dependencies

The site uses these vendor libraries:
- Bootstrap 5.3.3 - CSS framework
- Bootstrap Icons - Icon library
- AOS (Animate On Scroll) - Scroll animations
- Typed.js - Text typing animations
- Glightbox - Image lightbox
- Swiper - Touch slider
- Waypoints - Scroll-triggered events

## Development Commands

Since this is a static HTML site, there are no build commands. Development workflow:

1. **Local Development**: Open HTML files directly in a browser or use a local server:
   ```bash
   # Python 3
   python -m http.server 8000
   
   # Python 2
   python -m SimpleHTTPServer 8000
   
   # Node.js (if http-server is installed)
   http-server
   ```

2. **Testing**: Manual testing in browsers; no automated test suite

3. **Deployment**: Upload files to any static hosting service (GitHub Pages, Netlify, etc.)

## Important Patterns

- All pages use consistent Bootstrap-based layout with header navigation
- Images and documents are organized by type in `assets/docs/` subdirectories
- The site uses hash-based navigation for single-page sections (#about, #resume, etc.)
- Contact form requires server-side PHP configuration (currently using placeholder email)
- Favicon is set to `Logo.png` across all pages

## Additional Project Components

The repository also contains:

1. **agent-ui/**: A Next.js React application for an AI agent playground interface
   - Built with TypeScript, React, and Tailwind CSS
   - Uses pnpm for package management
   - Components for chat interface, message handling, and session management

2. **serena/**: A Python-based code analysis and language server tool
   - Supports multiple programming languages via LSP
   - MCP (Model Context Protocol) server integration
   - Includes Docker support for containerized deployment

3. **Shell Scripts**: Various setup and management scripts for the serena tool
   - `setup_serena_complete.sh`, `start_serena.sh`, `stop_serena.sh`
   - MCP configuration scripts

## Contact Form Configuration

The contact form at `forms/contact.php` requires:
- Update `$receiving_email_address` from placeholder 'contact@example.com'
- Upload the PHP Email Form library to `assets/vendor/php-email-form/`
- Configure SMTP settings if needed (currently commented out)