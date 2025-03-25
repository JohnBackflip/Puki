import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import axios from 'axios';

interface Room {
  id: number;
  room_number: string;
  room_type: string;
  price_per_night: number;
  status: string;
}

const RoomList = () => {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [checkIn, setCheckIn] = useState<Date | null>(null);
  const [checkOut, setCheckOut] = useState<Date | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchRooms();
  }, []);

  const fetchRooms = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/rooms');
      setRooms(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch rooms');
      setLoading(false);
    }
  };

  const handleBookRoom = (room: Room) => {
    setSelectedRoom(room);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setSelectedRoom(null);
    setOpenDialog(false);
    setCheckIn(null);
    setCheckOut(null);
  };

  const handleConfirmBooking = async () => {
    if (!selectedRoom || !checkIn || !checkOut) return;

    try {
      await axios.post('http://localhost:8000/api/bookings', {
        room_id: selectedRoom.id,
        check_in_date: checkIn.toISOString(),
        check_out_date: checkOut.toISOString(),
      });
      handleCloseDialog();
      fetchRooms();
    } catch (err) {
      setError('Failed to book room');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'available':
        return 'success.main';
      case 'occupied':
        return 'error.main';
      default:
        return 'warning.main';
    }
  };

  if (loading) return <Typography>Loading...</Typography>;
  if (error) return <Typography color="error">{error}</Typography>;

  return (
    <>
      <Typography variant="h4" gutterBottom>
        Available Rooms
      </Typography>
      <Grid container spacing={3}>
        {rooms.map((room) => (
          <Grid item xs={12} sm={6} md={4} key={room.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">Room {room.room_number}</Typography>
                <Typography>Type: {room.room_type}</Typography>
                <Typography>Price: ${room.price_per_night}/night</Typography>
                <Typography sx={{ color: getStatusColor(room.status) }}>
                  Status: {room.status}
                </Typography>
                <Button
                  variant="contained"
                  color="primary"
                  fullWidth
                  sx={{ mt: 2 }}
                  onClick={() => handleBookRoom(room)}
                  disabled={room.status.toLowerCase() !== 'available'}
                >
                  Book Now
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>Book Room</DialogTitle>
        <DialogContent>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label="Check-in Date"
              value={checkIn}
              onChange={(newValue) => setCheckIn(newValue)}
            />
            <DatePicker
              label="Check-out Date"
              value={checkOut}
              onChange={(newValue) => setCheckOut(newValue)}
              minDate={checkIn || undefined}
            />
          </LocalizationProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleConfirmBooking}
            color="primary"
            disabled={!checkIn || !checkOut}
          >
            Confirm Booking
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default RoomList; 