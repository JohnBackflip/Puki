import React from 'react';
import { Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button } from '@mui/material';

const Navigation = () => {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Hotel Management System
        </Typography>
        <Button color="inherit" component={Link} to="/">
          Rooms
        </Button>
        <Button color="inherit" component={Link} to="/bookings">
          Bookings
        </Button>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation; 