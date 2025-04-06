import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Container, CssBaseline } from '@mui/material';
import RoomList from './components/RoomList';
import BookingList from './components/BookingList';
import Navigation from './components/Navigation';

function App() {
  return (
    <Router>
      <CssBaseline />
      <Navigation />
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Routes>
          <Route path="/" element={<RoomList />} />
          <Route path="/bookings" element={<BookingList />} />
        </Routes>
      </Container>
    </Router>
  );
}

export default App; 