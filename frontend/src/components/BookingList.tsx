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
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import axios from 'axios';

interface Booking {
  id: number;
  room_id: number;
  check_in_date: string;
  check_out_date: string;
  status: string;
  total_price: number;
}

const BookingList = () => {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/bookings');
      setBookings(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch bookings');
      setLoading(false);
    }
  };

  const handlePayment = (booking: Booking) => {
    setSelectedBooking(booking);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setSelectedBooking(null);
    setOpenDialog(false);
    setPaymentMethod('');
  };

  const handleConfirmPayment = async () => {
    if (!selectedBooking || !paymentMethod) return;

    try {
      await axios.post('http://localhost:8000/api/payments', {
        booking_id: selectedBooking.id,
        payment_method: paymentMethod,
        amount: selectedBooking.total_price,
      });
      handleCloseDialog();
      fetchBookings();
    } catch (err) {
      setError('Failed to process payment');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed':
        return 'success.main';
      case 'pending':
        return 'warning.main';
      case 'cancelled':
        return 'error.main';
      default:
        return 'text.primary';
    }
  };

  if (loading) return <Typography>Loading...</Typography>;
  if (error) return <Typography color="error">{error}</Typography>;

  return (
    <>
      <Typography variant="h4" gutterBottom>
        Your Bookings
      </Typography>
      <Grid container spacing={3}>
        {bookings.map((booking) => (
          <Grid item xs={12} sm={6} md={4} key={booking.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">Booking #{booking.id}</Typography>
                <Typography>Room: {booking.room_id}</Typography>
                <Typography>Check-in: {new Date(booking.check_in_date).toLocaleDateString()}</Typography>
                <Typography>Check-out: {new Date(booking.check_out_date).toLocaleDateString()}</Typography>
                <Typography>Total: ${booking.total_price}</Typography>
                <Typography sx={{ color: getStatusColor(booking.status) }}>
                  Status: {booking.status}
                </Typography>
                {booking.status.toLowerCase() === 'pending' && (
                  <Button
                    variant="contained"
                    color="primary"
                    fullWidth
                    sx={{ mt: 2 }}
                    onClick={() => handlePayment(booking)}
                  >
                    Pay Now
                  </Button>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>Process Payment</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Payment Method</InputLabel>
            <Select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
              label="Payment Method"
            >
              <MenuItem value="credit_card">Credit Card</MenuItem>
              <MenuItem value="debit_card">Debit Card</MenuItem>
              <MenuItem value="paypal">PayPal</MenuItem>
            </Select>
          </FormControl>
          {selectedBooking && (
            <Typography sx={{ mt: 2 }}>
              Amount to pay: ${selectedBooking.total_price}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleConfirmPayment}
            color="primary"
            disabled={!paymentMethod}
          >
            Confirm Payment
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default BookingList; 