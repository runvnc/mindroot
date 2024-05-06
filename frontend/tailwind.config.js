module.exports = {
  purge: [],
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
      },
      backgroundColor: {
        box: 'var(--bg-box)',
      },
      borderColor: {
        default: 'var(--border-color)',
      },
      boxShadow: {
        'neon-bloom': 'var(--shadow-neon-bloom)',
      },
      borderRadius: {
        'theme': 'var(--border-radius)',
      },
      fontSize: {
        base: 'var(--font-size-base)',
      },
      padding: {
        theme: 'var(--padding-theme)',
      },
      margin: {
        theme: 'var(--margin-theme)',
      },
    },
  },
  variants: {
    extend: {},
  },
  plugins: [],
}
