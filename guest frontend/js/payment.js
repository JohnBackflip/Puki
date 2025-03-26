const stripe = Stripe('pk_test_51QAsReGgLeDXJUjvDrRwiHI6nisUuA7gSQw3AlX2UBqzlc4vPhbGCQCjcNiDel8pBfks9UhZGZXlO0jkvuNx1roP00zHKPl3aR'); // Replace with your Stripe publishable key
const elements = stripe.elements();

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
cardElement.mount("#card-element"); // Create a div with id="card-element" in your HTML for this to render

document.querySelectorAll(".btn.btn-confirm").forEach(button => {
    button.addEventListener("click", async function () {
        const amount = this.dataset.amount;
        const currency = this.dataset.currency;
        const description = this.dataset.description;

        try {
            // Call OutSystems API to create PaymentIntent
            const response = await fetch("https://personal-xnaxqorr.outsystemscloud.com/PaymentAPI/rest/PaymentAPI/PostPaymentIntents", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    amount: parseInt(amount), // Amount in cents
                    currency: currency,
                    description: description,
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`API returned status ${response.status}. Response: ${errorText}`);
                const result = JSON.parse(errorText);
                if (result && result.Errors) {
                    alert(`An error occurred: ${result.Errors[0]}`);
                } else {
                    alert(`An error occurred: ${errorText}`);
                }
                throw new Error(`API returned status ${response.status}. Response: ${errorText}`);
            }

            const result = await response.json();
            console.log("API Response:", result);
            console.log("API client:", result.client_secret);

            if (result && result.client_secret) {
                // Confirm the payment with Stripe Elements
                const { paymentIntent, error } = await stripe.confirmCardPayment(result.client_secret, {
                    payment_method: {
                        card: cardElement,
                        billing_details: {
                            name: document.querySelector("#cardName").value,
                            email: document.querySelector("#email").value,
                        },
                    },
                });

                if (error) {
                    console.error("Error confirming payment:", error);
                    alert(`Payment failed: ${error.message}`);
                } else {
                    if (paymentIntent.status === 'succeeded') {
                        alert("Payment Successful")
                        console.log("Payment successful:", paymentIntent);
                        // Handle successful payment here (e.g., display a success message, update booking status)
                    }
                }
            } else {
                throw new Error("Client secret not returned from API.");
            }
        } catch (error) {
            console.error("Error:", error);
            alert(`An error occurred while processing payment: ${error.message}`);
        }
    });
});
