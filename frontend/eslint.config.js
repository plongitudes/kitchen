import js from '@eslint/js'
import globals from 'globals'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import unusedImports from 'eslint-plugin-unused-imports'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'node_modules', '.vite']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs['recommended-latest'],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    plugins: {
      react,
      'unused-imports': unusedImports,
    },
    rules: {
      // Disable the base rule as it can report incorrect errors
      'no-unused-vars': 'off',
      // Use unused-imports rules instead
      'unused-imports/no-unused-imports': 'warn',
      'unused-imports/no-unused-vars': [
        'warn',
        {
          vars: 'all',
          varsIgnorePattern: '^_',
          args: 'after-used',
          argsIgnorePattern: '^_',
        },
      ],
      // Enable React rules to detect JSX usage
      'react/jsx-uses-react': 'error',
      'react/jsx-uses-vars': 'error',
      // Enforce using centralized API instance instead of direct axios imports
      'no-restricted-imports': ['error', {
        paths: [{
          name: 'axios',
          message: 'Import api from "../services/api" instead of using axios directly. The api instance has interceptors for auth and runtime config.',
        }],
      }],
    },
  },
])
