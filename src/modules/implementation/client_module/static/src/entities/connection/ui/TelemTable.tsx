import { Table, TableBody, TableCell, TableRow, TableContainer, Paper, Typography } from '@mui/material';
import { observer } from 'mobx-react-lite';
import { connectionStore } from '../model/connection.store';

const formatValue = (value: unknown): React.ReactNode => {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'object') {
    return <pre style={{ margin: 0, fontSize: '0.75rem' }}>{JSON.stringify(value, null, 2)}</pre>;
  }
  if (typeof value === 'boolean') {
    return (
      <Typography component="span" color={value ? 'success.main' : 'error.main'}>
        {String(value)}
      </Typography>
    );
  }
  if (typeof value === 'number') {
    return (
      <Typography component="span" color="primary.main">
        {value}
      </Typography>
    );
  }
  return String(value);
};

const TelemTableInner = () => {
  const telem = connectionStore.telem;
  const entries = Object.entries(telem);

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableBody>
          {entries.map(([key, value]) => (
            <TableRow key={key}>
              <TableCell sx={{ color: 'text.secondary', width: '50%' }}>{key}:</TableCell>
              <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.85rem', width: '50%' }}>
                {formatValue(value)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export const TelemTable = observer(TelemTableInner);
