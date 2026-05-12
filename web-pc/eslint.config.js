import globals from 'globals'
import pluginVue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'
import vueParser from 'vue-eslint-parser'

export default tseslint.config(
  // TypeScript / JavaScript files
  {
    files: ['src/**/*.{ts,js,mjs,cjs}'],
    languageOptions: {
      globals: globals.browser,
      parserOptions: {
        project: './tsconfig.app.json',
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': 'warn',
      'no-console': 'off',
    },
  },
  // Vue SFC files
  {
    files: ['src/**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint.parser,
        project: './tsconfig.app.json',
        tsconfigRootDir: import.meta.dirname,
        extraFileExtensions: ['.vue'],
      },
      globals: globals.browser,
    },
    plugins: {
      vue: pluginVue,
      '@typescript-eslint': tseslint.plugin,
    },
    rules: {
      ...pluginVue.configs['flat/recommended'].rules,
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': 'warn',
      'no-console': 'off',
    },
  },
)
