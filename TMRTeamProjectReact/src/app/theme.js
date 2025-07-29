import { createTheme } from '@mui/material';
import * as React from 'react';

const muiThemePaletteKeys = [
  'background',
  'error',
  'info',
  'primary',
  'secondary',
  'success',
  'text',
  'warning',
];

export default function RootTheme() {
  const theme = createTheme({
    typography: {
      fontFamily: 'GmarketSansMedium',
    },
    palette: {
      type: 'light',
      primary: {
        main: '#3f51b5',
      },
      secondary: {
        main: '#f50057',
      },
      background: {
        default: '#fff',
        paper: '#fff',
      },
    },
  });

  React.useEffect(() => {
    const r = document.querySelector(':root');
    muiThemePaletteKeys.forEach((paletteKey) => {
      const themeColorObj = theme.palette[paletteKey];
      // console.log(themeColor);
      for (const key in themeColorObj) {
        // console.log(key);
        if (Object.hasOwnProperty.call(themeColorObj, key)) {
          const colorVal = themeColorObj[key];
          r.style.setProperty(`--mui-color-${paletteKey}-${key}`, colorVal);
        }
      }
    });
  }, []);

  return theme;
}
