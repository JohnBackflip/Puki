document.addEventListener("DOMContentLoaded", function () {
    const roomType = localStorage.getItem("roomType") || "State Room Suite King";
    const checkIn = localStorage.getItem("checkInDate") || "Not specified";
    const checkOut = localStorage.getItem("checkOutDate") || "Not specified";
    const adults = localStorage.getItem("adults") || "0";
    const children = localStorage.getItem("children") || "0";
    const roomPrice = localStorage.getItem("roomPrice") || "0";
    const roomImage = localStorage.getItem("roomImage") || "images/default.jpg";

    const checkInDate = new Date(checkIn);
    const checkOutDate = new Date(checkOut);
    const timeDiff = checkOutDate - checkInDate;
    const nights = Math.max(1, Math.ceil(timeDiff / (1000 * 60 * 60 * 24)));
    const totalCost = (parseFloat(roomPrice) * nights).toFixed(2);

    const arrival = document.getElementById("arrivalDate");
    const departure = document.getElementById("departureDate");
    const guestCount = document.getElementById("guestCount");
    const type = document.getElementById("roomType");
    const cost = document.getElementById("totalCost");
    const image = document.getElementById("roomImage");
    const hotelName = document.getElementById("hotelName");

    if (arrival) arrival.textContent = checkIn;
    if (departure) departure.textContent = checkOut;
    if (guestCount) guestCount.textContent = `${adults} Adults, ${children} Children`;
    if (type) type.textContent = roomType;
    if (cost) cost.textContent = totalCost;
    if (image) {
        image.src = roomImage;
        image.alt = `${roomType} Image`;
    }
    if (hotelName) hotelName.textContent = "Puki Hotel";
});

async function getOrCreateGuest(name, email, contact) {
    try {
        const res = await fetch("http://localhost:5011/guest");
        if (!res.ok) throw new Error("Failed to fetch guest list");

        const data = await res.json();
        const guests = data.data.guests;

        const existingGuest = guests.find(
            g => g.name.toLowerCase() === name.toLowerCase() && g.email.toLowerCase() === email.toLowerCase()
        );

        if (existingGuest) return existingGuest.guest_id;

        const payload = { name, email, contact };
        console.log("Creating guest with payload:", payload);

        const createRes = await fetch("http://localhost:5011/createGuest", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!createRes.ok) throw new Error("Guest creation failed");
        const newGuest = await createRes.json();
        return newGuest.data.guest_id;

    } catch (error) {
        console.error("Guest check/create failed:", error);
        alert("There was an issue processing your guest information.");
        return null;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const confirmBtn = document.getElementById("confirmBookingBtn");

    if (!confirmBtn) {
        console.error("Confirm button not found.");
        return;
    }

    confirmBtn.addEventListener("click", async () => {
        const fullName = document.getElementById("fullName").value.trim();
        const email = document.getElementById("email").value.trim();
        const countryCode = document.getElementById("countryCode").value;
        const localNumber = document.getElementById("localNumber").value.trim();
        const contact = `${countryCode}${localNumber}`;

        let roomTypeRaw = localStorage.getItem("roomType") || "";
        let roomType;

        if (roomTypeRaw.includes("Single")) roomType = "Single";
        else if (roomTypeRaw.includes("Family")) roomType = "Family";
        else if (roomTypeRaw.includes("Presidential")) roomType = "PresidentialSuite";
        else roomType = roomTypeRaw.trim();  

        const price = parseFloat(localStorage.getItem("roomPrice") || "0");
        // Parse the raw dates from localStorage
        const rawCheckIn = localStorage.getItem("checkInDate");
        const rawCheckOut = localStorage.getItem("checkOutDate");

        // Add 1 day and format to YYYY-MM-DD
        const checkInDate = new Date(rawCheckIn);
        checkInDate.setDate(checkInDate.getDate() + 1);

        const checkOutDate = new Date(rawCheckOut);
        checkOutDate.setDate(checkOutDate.getDate() + 1);

        const checkIn = checkInDate.toISOString().split("T")[0];
        const checkOut = checkOutDate.toISOString().split("T")[0];

        if (!fullName || !email || !contact || !roomType || !checkIn || !checkOut || !price) {
            alert("Please fill in all required fields.");
            return;
        }

        try {
            const guestId = await getOrCreateGuest(fullName, email, contact);
            if (!guestId) return;

            const bookingPayload = {
                guest_id: guestId,
                room_type: roomType,
                check_in: checkIn,
                check_out: checkOut,
                price
            };

            console.log("Sending booking payload:", bookingPayload);

            const bookingRes = await fetch("http://localhost:5013/makebooking", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(bookingPayload)
            });

            const bookingData = await bookingRes.json();
            if (bookingRes.status !== 201 && bookingRes.status !== 200) {
                throw new Error(bookingData.message || "Booking failed");
            }
            const booking = bookingData.data;

            localStorage.setItem("bookingDetails", JSON.stringify({
                bookingId: booking.booking_id,
                totalCost: booking.price
            }));

            // Optionally store guest info too
            localStorage.setItem("fullName", document.getElementById("fullName").value);
            localStorage.setItem("email", document.getElementById("email").value);
            localStorage.setItem("phoneNumber", document.getElementById("localNumber").value);

            alert("Booking confirmed!");
            window.location.href = "bookingconfirmation.html";
        } catch (err) {
            console.error(err);
            alert("Booking failed. Please try again.");
        }
    });
});