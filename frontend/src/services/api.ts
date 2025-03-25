import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface Room {
  id: number;
  room_number: string;
  room_type: string;
  price_per_night: string;
  floor: number;
  status: string;
  created_at: string;
}

export interface Booking {
  id: number;
  room_id: number;
  guest_id: number;
  check_in_date: string;
  check_out_date: string;
  status: string;
  total_price: string;
  created_at: string;
}

export interface Payment {
  id: number;
  booking_id: number;
  amount: string;
  status: string;
  payment_method: string;
  created_at: string;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const roomService = {
  listRooms: async () => {
    const response = await api.get<Room[]>('/rooms/');
    return response.data;
  },

  getRoomById: async (id: number) => {
    const response = await api.get<Room>(`/rooms/${id}`);
    return response.data;
  },

  checkAvailability: async (roomId: number, startDate: string, endDate: string) => {
    const response = await api.get<boolean>(`/rooms/${roomId}/availability`, {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },

  updateRoomStatus: async (roomId: number, status: string) => {
    const response = await api.patch<Room>(`/rooms/${roomId}/status`, { status });
    return response.data;
  },
};

export const bookingService = {
  createBooking: async (bookingData: {
    room_id: number;
    check_in_date: string;
    check_out_date: string;
  }) => {
    const response = await api.post<Booking>('/bookings/', bookingData);
    return response.data;
  },

  getBookingById: async (id: number) => {
    const response = await api.get<Booking>(`/bookings/${id}`);
    return response.data;
  },

  listBookings: async () => {
    const response = await api.get<Booking[]>('/bookings/');
    return response.data;
  },
};

export const paymentService = {
  createPayment: async (paymentData: {
    booking_id: number;
    amount: string;
    payment_method: string;
  }) => {
    const response = await api.post<Payment>('/payments/', paymentData);
    return response.data;
  },

  getPaymentById: async (id: number) => {
    const response = await api.get<Payment>(`/payments/${id}`);
    return response.data;
  },
};

export default api; 