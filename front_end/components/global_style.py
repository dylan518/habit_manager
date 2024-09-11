# Common styles
COMMON_STYLES = """
/* Global styles and color variables */
:root {
  /* Color palette */
  --primary-color: #007bff;
  --secondary-color: #6c757d;
  --success-color: #28a745;
  --danger-color: #dc3545;
  --warning-color: #ffc107;
  --info-color: #17a2b8;
  --light-color: #f8f9fa;
  --dark-color: #343a40;

  /* Typography */
  --font-family-sans-serif: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-family-monospace: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  --font-size-base: 1rem;
  --line-height-base: 1.5;

  /* Spacing */
  --spacing-small: 0.5rem;
  --spacing-medium: 1rem;
  --spacing-large: 1.5rem;

  /* Border radius */
  --border-radius: 0.25rem;
}

/* Global reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-family-sans-serif);
  font-size: var(--font-size-base);
  line-height: var(--line-height-base);
  color: var(--dark-color);
  background-color: var(--light-color);
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
  margin-bottom: var(--spacing-medium);
  font-weight: 500;
  line-height: 1.2;
}

/* Links */
a {
  color: var(--primary-color);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

/* Buttons */
.btn {
  display: inline-block;
  font-weight: 400;
  text-align: center;
  white-space: nowrap;
  vertical-align: middle;
  user-select: none;
  border: 1px solid transparent;
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  line-height: 1.5;
  border-radius: var(--border-radius);
  transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.btn-primary {
  color: #fff;
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.btn-secondary {
  color: #fff;
  background-color: var(--secondary-color);
  border-color: var(--secondary-color);
}

/* Forms */
.form-control {
  display: block;
  width: 100%;
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  line-height: 1.5;
  color: var(--dark-color);
  background-color: #fff;
  background-clip: padding-box;
  border: 1px solid #ced4da;
  border-radius: var(--border-radius);
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

/* Utility classes */
.text-center {
  text-align: center;
}

.mt-1 { margin-top: var(--spacing-small); }
.mt-2 { margin-top: var(--spacing-medium); }
.mt-3 { margin-top: var(--spacing-large); }

.mb-1 { margin-bottom: var(--spacing-small); }
.mb-2 { margin-bottom: var(--spacing-medium); }
.mb-3 { margin-bottom: var(--spacing-large); }
"""
