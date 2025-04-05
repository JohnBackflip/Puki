document.addEventListener("DOMContentLoaded", function () {
    // Retrieve stored booking details
    const roomType = localStorage.getItem("roomType") || "State Room Suite King";
    const checkIn = localStorage.getItem("checkInDate") || "Not specified";
    const checkOut = localStorage.getItem("checkOutDate") || "Not specified";
    const adults = localStorage.getItem("adults") || "0";
    const children = localStorage.getItem("children") || "0";
    const roomPrice = localStorage.getItem("roomPrice") || "0";
    const roomImage = localStorage.getItem("roomImage") || "images/default.jpg";

    // Calculate total nights
    const checkInDate = new Date(checkIn);
    const checkOutDate = new Date(checkOut);
    const timeDiff = checkOutDate - checkInDate;
    const nights = Math.max(1, Math.ceil(timeDiff / (1000 * 60 * 60 * 24))); // Ensure at least 1 night
    const totalCost = (parseFloat(roomPrice) * nights).toFixed(2);

    // Store the relevant details in localStorage for later use in the payment process
    localStorage.setItem("totalCost", totalCost);
    localStorage.setItem("roomType", roomType);

    // Update the booking summary
    document.getElementById("arrivalDate").textContent = checkIn;
    document.getElementById("departureDate").textContent = checkOut;
    document.getElementById("guestCount").textContent = `${adults} Adults, ${children} Children`;
    document.getElementById("roomType").textContent = roomType;
    document.getElementById("totalCost").textContent = totalCost;
    document.getElementById("nights").textContent = nights;

    // Update room image
    const roomImageElement = document.getElementById("roomImage");
    if (roomImageElement) {
        roomImageElement.src = roomImage;
        roomImageElement.alt = `${roomType} Image`;
    }

    document.getElementById("hotelName").textContent = "Puki Hotel";
});
