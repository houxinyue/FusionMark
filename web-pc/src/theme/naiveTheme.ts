import { type GlobalThemeOverrides } from 'naive-ui'

export const fusionMarkTheme = null

export const fusionMarkThemeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#f97316',
    primaryColorHover: '#fb923c',
    primaryColorPressed: '#c2410c',
    primaryColorSuppl: '#fdba74',
    infoColor: '#0ea5e9',
    successColor: '#16a34a',
    warningColor: '#d97706',
    errorColor: '#e11d48',
    borderRadius: '6px',
    borderColor: 'rgba(148, 163, 184, 0.28)',
    textColorBase: '#334155',
    bodyColor: '#f8fafc',
    cardColor: '#ffffff',
    modalColor: '#ffffff',
    popoverColor: '#ffffff',
  },
  Button: {
    borderRadiusMedium: '6px',
    borderRadiusSmall: '5px',
    textColorPrimary: '#ffffff',
    textColorHoverPrimary: '#ffffff',
    textColorPressedPrimary: '#ffffff',
    colorPrimary: '#f97316',
    colorHoverPrimary: '#fb923c',
    colorPressedPrimary: '#c2410c',
    colorFocusPrimary: '#f97316',
    borderPrimary: '1px solid rgba(249, 115, 22, 0.58)',
    borderHoverPrimary: '1px solid rgba(251, 146, 60, 0.82)',
    boxShadowFocusPrimary: '0 0 0 3px rgba(249, 115, 22, 0.18)',
  },
  Input: {
    borderRadius: '6px',
    color: '#ffffff',
    colorFocus: '#ffffff',
    border: '1px solid rgba(148, 163, 184, 0.32)',
    borderHover: '1px solid rgba(251, 146, 60, 0.52)',
    borderFocus: '1px solid rgba(249, 115, 22, 0.78)',
    boxShadowFocus: '0 0 0 3px rgba(249, 115, 22, 0.14)',
  },
  Modal: {
    borderRadius: '10px',
  },
  Card: {
    borderRadius: '8px',
    color: '#ffffff',
    borderColor: 'rgba(148, 163, 184, 0.28)',
  },
  Tag: {
    borderRadius: '4px',
  },
}
