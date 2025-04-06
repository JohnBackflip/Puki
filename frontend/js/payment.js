// const stripe = Stripe("pk_test_51QAsReGgLeDXJUjvDrRwiHI6nisUuA7gSQw3AlX2UBqzlc4vPhbGCQCjcNiDel8pBfks9UhZGZXlO0jkvuNx1roP00zHKPl3aR"); // Replace with your Stripe publishable key
// const elements = stripe.elements();

const style = {
    base: {
        color: "#32325d",
        fontFamily: "'Helvetica Neue', Helvetica, sans-serif",
        fontSize: "16px",
        "::placeholder": {
            color: "#aab7c4",
        },
        padding: "10px",
        border: "1px solid #ccc",
        borderRadius: "5px",
    },
    invalid: {
        color: "#fa755a",
    },
};

const cardElement = elements.create("card", { style });
cardElement.mount("#card-element");

// document.querySelectorAll(".btn.btn-confirm").forEach(button => {
//     button.addEventListener("click", async function () {
        
//         // Retrieve guest details from the form
//         const fullName = document.getElementById("fullName")?.value.trim() || "";
//         const email = document.getElementById("email")?.value.trim() || "";
//         const countryCode = document.getElementById("countryCode")?.value.trim() || "";
//         const localNumber = document.getElementById("localNumber")?.value.trim() || "";
//         const phoneNumber = countryCode && localNumber ? `${countryCode} ${localNumber}` : "";

//         // Save guest details to localStorage
//         localStorage.setItem("fullName", fullName);
//         localStorage.setItem("email", email);
//         localStorage.setItem("phoneNumber", phoneNumber);

//         // Retrieve other details needed for payment from localStorage
//         const totalCost = localStorage.getItem("totalCost");
//         const roomType = localStorage.getItem("roomType");
//         const checkInDate = localStorage.getItem("checkInDate");
//         const checkOutDate = localStorage.getItem("checkOutDate");

//         // Calculate the amount in cents
//         const amount = parseFloat(totalCost) * 100;

//         try {
//             const response = await fetch("https://personal-xnaxqorr.outsystemscloud.com/PaymentAPI/rest/PaymentAPI/PostPaymentIntents", {
//                 method: "POST",
//                 headers: {
//                     "Content-Type": "application/json",
//                 },
//                 body: JSON.stringify({
//                     amount: parseInt(amount),
//                     currency: "SGD",
//                     description: roomType,
//                     checkInDate,
//                     checkOutDate,
//                 }),
//             });

//             if (!response.ok) {
//                 const errorText = await response.text();
//                 console.error(`API returned status ${response.status}. Response: ${errorText}`);
//                 alert(`An error occurred: ${errorText}`);
//                 throw new Error(`API returned status ${response.status}. Response: ${errorText}`);
//             }

//             const result = await response.json();
//             console.log("API Response:", result);

//             if (result && result.client_secret) {
//                 const { paymentIntent, error } = await stripe.confirmCardPayment(result.client_secret, {
//                     payment_method: {
//                         card: cardElement,
//                         billing_details: {
//                             name: fullName,
//                             email: email,
//                         },
//                     },
//                 });

//                 if (error) {
//                     console.error("Error confirming payment:", error);
//                     alert(`Payment failed: ${error.message}`);
//                 } else {
//                     if (paymentIntent.status === 'succeeded') {
//                         console.log("Redirecting to bookingconfirmation.html...");

//                         // Generate a random 3-digit customer ID
//                         const customerId = Math.floor(100 + Math.random() * 900);

//                         // Generate a random 5-digit booking ID
//                         const bookingId = Math.floor(10000 + Math.random() * 90000);

//                         // Store booking details in localStorage
//                         const bookingDetails = {
//                             bookingId,
//                             customerId,
//                             checkInDate,
//                             checkOutDate,
//                             roomType,
//                             fullName: localStorage.getItem("fullName") || "Not provided",
//                             email: localStorage.getItem("email") || "Not provided",
//                             phoneNumber: localStorage.getItem("phoneNumber") || "Not provided",
//                             totalCost: (amount / 100).toFixed(2),
//                         };
//                         localStorage.setItem("bookingDetails", JSON.stringify(bookingDetails));

//                         // Redirect to confirmation page
//                         window.location.href = "bookingconfirmation.html";
//                     }
//                 }
//             } else {
//                 throw new Error("Client secret not returned from API.");
//             }
//         } catch (error) {
//             console.error("Error:", error);
//             alert(`An error occurred while processing payment: ${error.message}`);
//         }
//     });
// });
